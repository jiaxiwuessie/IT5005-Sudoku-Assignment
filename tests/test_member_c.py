"""Member C regression checks. Run: python -m unittest discover -s tests -v."""
import unittest
from unittest.mock import patch

import sudoku_solver as solver
from logic_ import Expr, PropDefiniteKB, pl_fc_entails


class ForwardChainingTests(unittest.TestCase):
    def test_single_shared_library_pass(self):
        # A completed Latin-pattern Sudoku with an initially missing last cell.
        solution = {(r, c): ((r - 1) * 2 + (r - 1) // 2 + c - 1) % 4 + 1
                    for r in range(1, 5) for c in range(1, 5)}
        givens = {cell: v for cell, v in solution.items() if cell != (4, 4)}
        before = dict(givens)
        with patch.object(solver, 'pl_fc_entails', wraps=pl_fc_entails) as fc:
            self.assertEqual(solver.solve_full_grid_fc(4, 2, 2, givens), solution)
            self.assertEqual(fc.call_count, 1)
        self.assertEqual(givens, before)
        # Compare the captured closure with the untouched library for every
        # correct AND incorrect candidate on a small puzzle.
        original = solver.build_definite_kb(4, 2, 2, givens)
        observed = solver._ObservedFCKB(original)
        self.assertFalse(pl_fc_entails(observed, Expr('AbsentMarker')))
        for r in range(1, 5):
            for c in range(1, 5):
                for v in range(1, 5):
                    query = solver.atom('Is', r, c, v)
                    self.assertEqual(query in observed.processed,
                                     pl_fc_entails(original, query))

    def test_rectangular_boxes(self):
        solution = {(r, c): ((r - 1) * 3 + (r - 1) // 2 + c - 1) % 6 + 1
                    for r in range(1, 7) for c in range(1, 7)}
        givens = {cell: v for cell, v in solution.items() if cell != (6, 6)}
        self.assertEqual(solver.solve_full_grid_fc(6, 2, 3, givens), solution)

    def test_stalled_and_contradictory_puzzles_do_not_return_guessed_grids(self):
        with self.assertRaises(ValueError):
            solver.solve_full_grid_fc(4, 2, 2, {})
        with self.assertRaises(ValueError):
            solver.solve_full_grid_fc(4, 2, 2, {(1, 1): 1, (1, 2): 1})

    def test_trace_is_a_real_ordered_proof_and_kb_is_unchanged(self):
        kb = PropDefiniteKB()
        p, q, r, unrelated = map(Expr, ['TestP', 'TestQ', 'TestR', 'TestOther'])
        for sentence in [p, Expr('==>', p, q), Expr('==>', q & p, r),
                         Expr('==>', r, q), unrelated]:
            kb.tell(sentence)
        before = list(kb.clauses)
        for query in [p, q, r, Expr('Unknown')]:
            entailed, proof = solver.trace_fc_query(kb, query)
            self.assertEqual(entailed, pl_fc_entails(kb, query))
            available = set()
            for step in proof:
                self.assertTrue(set(step['premises']) <= available)
                if step['rule'] is None:
                    self.assertIn(step['conclusion'], kb.clauses)
                else:
                    self.assertIn(step['rule'], kb.clauses)
                    self.assertEqual(step['rule'].args[1], step['conclusion'])
                available.add(step['conclusion'])
            self.assertEqual(query in available, entailed)
            self.assertNotIn(unrelated, available)
        self.assertEqual(kb.clauses, before)


if __name__ == '__main__':
    unittest.main()
