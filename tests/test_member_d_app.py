"""Exercise the real Streamlit UI and proof explanations, without a web server."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
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
    def test_solver_never_needs_reference_solutions(self):
        raw_pool = json.loads((ROOT / 'puzzles.json').read_text())
        expected = {tuple(map(int, k.split('_'))): v
                    for k, v in raw_pool['puzzles'][0]['solution'].items()}
        for puzzle in raw_pool['puzzles']:
            puzzle.pop('solution')
        with patch('json.load', return_value=raw_pool):
            at = AppTest.from_file(str(ROOT / 'sudoku_app.py'), default_timeout=30).run()
            next(b for b in at.button if b.label == 'Solve puzzle').click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertEqual(at.session_state['solve_result']['grid'], expected)

    def test_readable_proof_and_accessible_board(self):
        at = AppTest.from_file(str(ROOT / 'sudoku_app.py'), default_timeout=30).run()
        self.assertEqual(at.title[0].value, 'Sudoku Solver')
        html = next(m.value for m in at.markdown if '<table ' in m.value)
        self.assertEqual(html.count('<td '), 81)
        self.assertIn('aria-label="Row 1, column 2: 3, given"', html)
        self.assertIn('box-bottom', html)
        self.assertIn('box-right', html)
        next(b for b in at.button if b.label == 'Check entailment').click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertTrue(at.session_state['query_result']['verdict'])
        labels = [e.label for e in at.expander]
        for kind in ['Given', 'Row exclusion', 'Column exclusion', 'Box exclusion', 'Last candidate']:
            self.assertTrue(any(kind in label for label in labels), kind)
        self.assertTrue(any('Premise: R1C1 cannot be 2' in m.value for m in at.markdown))
        self.assertTrue(any('Conclusion: R1C1 is 1' in m.value for m in at.markdown))


if __name__ == '__main__':
    unittest.main()
