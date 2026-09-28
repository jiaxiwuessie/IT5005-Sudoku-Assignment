"""Exercise the real Streamlit UI and proof explanations, without a web server."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import sudoku_app as app
from sudoku_solver import atom, build_definite_kb, trace_fc_query


class AppWorkflowTests(unittest.TestCase):
    def create_app(self):
        at = AppTest.from_file(str(ROOT / 'sudoku_app.py'), default_timeout=30).run()
        self.assertEqual(len(at.exception), 0)
        return at

    def click(self, at, label):
        next(b for b in at.button if b.label == label).click().run()
        self.assertEqual(len(at.exception), 0)
        return at

    def test_both_solvers_and_puzzle_switch(self):
        at = self.create_app()
        pool = json.loads((ROOT / 'puzzles.json').read_text())
        for index in range(5):
            at.selectbox(key='puzzle_selection').select(index).run()
            self.assertNotIn('solve_result', at.session_state)
            self.assertNotIn('query_result', at.session_state)
            expected = {tuple(map(int, k.split('_'))): v
                        for k, v in pool['puzzles'][index]['solution'].items()}
            for algorithm in ['Forward chaining', 'Backward chaining']:
                at.radio(key='algorithm').set_value(algorithm).run()
                self.click(at, 'Solve puzzle')
                result = at.session_state['solve_result']
                self.assertEqual(result['grid'], expected)
                self.assertEqual(result['algorithm'], algorithm)
                self.assertGreater(result['seconds'], 0)
            self.click(at, 'Reset this puzzle')
            self.assertNotIn('solve_result', at.session_state)

    def test_queries_replay_and_reset(self):
        at = self.create_app()
        self.click(at, 'Check entailment')
        result = at.session_state['query_result']
        self.assertTrue(result['verdict'])
        self.assertEqual(result['query'], (1, 1, 1))
        self.assertEqual(str(result['steps'][-1]['conclusion']), 'Is1_1_1')
        self.assertTrue(any('not the backward search log' in c.value for c in at.caption))
        at.slider[0].set_value(1).run()
        self.assertEqual(at.slider[0].value, 1)
        self.assertTrue(any('Step 1 of' in m.value for m in at.markdown))
        at.number_input(key='query_value').set_value(2)
        self.click(at, 'Check entailment')
        self.assertFalse(at.session_state['query_result']['verdict'])
        self.assertEqual(at.session_state['query_result']['steps'], [])
        self.assertEqual(len(at.slider), 0)
        self.assertTrue(any('not, by itself' in c.value for c in at.caption))
        at.number_input(key='query_col').set_value(2)
        at.number_input(key='query_value').set_value(3)
        self.click(at, 'Check entailment')
        self.assertTrue(at.session_state['query_result']['verdict'])
        self.assertEqual(len(at.session_state['query_result']['steps']), 1)
        self.assertEqual(len(at.slider), 0)
        self.click(at, 'Reset this puzzle')
        self.assertNotIn('query_result', at.session_state)
        self.click(at, 'Check entailment')
        at.selectbox(key='puzzle_selection').select(1).run()
        self.assertNotIn('query_result', at.session_state)

    def test_failures_are_presented_without_stale_success(self):
        at = self.create_app()
        self.click(at, 'Solve puzzle')
        with patch('sudoku_solver.solve_full_grid_fc', side_effect=ValueError('Test failure')):
            self.click(at, 'Solve puzzle')
        self.assertNotIn('solve_result', at.session_state)
        self.assertTrue(any('Test failure' in e.value for e in at.error))
        with patch('sudoku_solver.trace_fc_query', return_value=(False, [])):
            self.click(at, 'Check entailment')
        self.assertNotIn('query_result', at.session_state)
        self.assertTrue(any('disagree' in e.value for e in at.error))


class PresentationTests(unittest.TestCase):
    def test_loader_and_validation_never_need_reference_solutions(self):
        n, bh, bw, puzzles = app.load_puzzles(ROOT / 'puzzles.json')
        self.assertEqual([len(p) for p in puzzles], [30, 33, 36, 39, 42])
        self.assertFalse(app.valid_grid(puzzles[0], n, bh, bw, puzzles[0]))
        raw = json.loads((ROOT / 'puzzles.json').read_text())
        solution = {tuple(map(int, k.split('_'))): v for k, v in raw['puzzles'][0]['solution'].items()}
        self.assertTrue(app.valid_grid(solution, n, bh, bw, puzzles[0]))
        solution[(1, 1)] = solution[(1, 2)]
        self.assertFalse(app.valid_grid(solution, n, bh, bw, puzzles[0]))

    def test_trace_transcript_is_actual_proof_and_board_accessible(self):
        n, bh, bw, puzzles = app.load_puzzles(ROOT / 'puzzles.json')
        verdict, steps = trace_fc_query(build_definite_kb(n, bh, bw, puzzles[0]), atom('Is', 1, 1, 1))
        self.assertTrue(verdict)
        text = app.proof_text(steps, bh, bw)
        self.assertIn('R1C1 is 1', text)
        self.assertIn('Last candidate', text)
        for kind in ['Given', 'Row exclusion', 'Column exclusion', 'Box exclusion']:
            self.assertIn(kind, text)
        html = app.board_html(n, bh, bw, puzzles[0])
        self.assertEqual(html.count('<td '), 81)
        self.assertIn('aria-label="Row 1, column 2: 3, given"', html)
        self.assertIn('box-bottom', html)
        self.assertIn('box-right', html)


if __name__ == '__main__':
    unittest.main()
