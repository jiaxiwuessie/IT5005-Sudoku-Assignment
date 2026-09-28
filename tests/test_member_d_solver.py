"""Integration checks for the solver contracts used by the Streamlit tutor.

Run with: python -m unittest discover -s tests -v
The reference solutions are used only for assertions after inference.
"""

import json
from pathlib import Path
import random
import unittest

import sudoku_solver as solver
from logic_ import Expr, PropDefiniteKB, parse_definite_clause


def coordinates(mapping):
    return {tuple(map(int, key.split('_'))): value
            for key, value in mapping.items()}


class TutorSolverIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / 'puzzles.json'
        cls.bank = json.loads(source.read_text(encoding='utf-8'))

    def test_all_puzzles_and_all_bc_candidates(self):
        bank = self.bank
        n, box_h, box_w = bank['n'], bank['box_h'], bank['box_w']
        for index, puzzle in enumerate(bank['puzzles']):
            with self.subTest(puzzle=index):
                givens = coordinates(puzzle['givens'])
                expected = coordinates(puzzle['solution'])
                before = dict(givens)
                for solve in (solver.solve_full_grid_fc,
                              solver.solve_full_grid_bc):
                    result = solve(n, box_h, box_w, givens)
                    self.assertEqual(result, expected)
                    self.assertEqual(givens, before)
                    digits = set(range(1, n + 1))
                    for r in range(1, n + 1):
                        self.assertEqual({result[r, c] for c in digits}, digits)
                    for c in range(1, n + 1):
                        self.assertEqual({result[r, c] for r in digits}, digits)
                    for br in range(1, n + 1, box_h):
                        for bc in range(1, n + 1, box_w):
                            self.assertEqual(
                                {result[r, c]
                                 for r in range(br, br + box_h)
                                 for c in range(bc, bc + box_w)}, digits)
                kb = solver.build_definite_kb(n, box_h, box_w, givens)
                for r in range(1, n + 1):
                    for c in range(1, n + 1):
                        for v in range(1, n + 1):
                            query = solver.atom('Is', r, c, v)
                            self.assertEqual(
                                solver.pl_bc_entails(kb, query),
                                expected[r, c] == v, (index, r, c, v))

    def test_bank_proofs_contain_real_rules_and_only_available_premises(self):
        bank = self.bank
        for index, puzzle in enumerate(bank['puzzles']):
            with self.subTest(puzzle=index):
                givens = coordinates(puzzle['givens'])
                expected = coordinates(puzzle['solution'])
                kb = solver.build_definite_kb(
                    bank['n'], bank['box_h'], bank['box_w'], givens)
                before = list(kb.clauses)
                cell = next(cell for cell in expected if cell not in givens)
                query = solver.atom('Is', *cell, expected[cell])
                entailed, proof = solver.trace_fc_query(kb, query)
                self.assertTrue(entailed)
                available = set()
                for step in proof:
                    self.assertTrue(set(step['premises']) <= available)
                    if step['rule'] is None:
                        self.assertIn(step['conclusion'], kb.clauses)
                    else:
                        self.assertIn(step['rule'], kb.clauses)
                        premises, conclusion = parse_definite_clause(step['rule'])
                        self.assertEqual(step['premises'], premises)
                        self.assertEqual(step['conclusion'], conclusion)
                    available.add(step['conclusion'])
                self.assertEqual(proof[-1]['conclusion'], query)
                self.assertIn(query, available)
                wrong_value = expected[cell] % bank['n'] + 1
                self.assertEqual(solver.trace_fc_query(
                    kb, solver.atom('Is', *cell, wrong_value)), (False, []))
                self.assertEqual(kb.clauses, before)

    def test_bc_cycles_and_alternatives_match_independent_horn_closure(self):
        # Seeded small Horn graphs exercise cyclic branches, alternative
        # proofs, AND premises, negative answers and reuse across queries.
        rng = random.Random(5005)
        atoms = [Expr('Check' + str(i)) for i in range(8)]
        for graph in range(60):
            kb = PropDefiniteKB()
            facts = set(rng.sample(atoms, rng.randrange(4)))
            rules = []
            for _ in range(20):
                premises = rng.sample(atoms, rng.randrange(1, 4))
                conclusion = rng.choice(atoms)
                rules.append((premises, conclusion))
                antecedent = premises[0]
                for premise in premises[1:]:
                    antecedent = antecedent & premise
                kb.tell(Expr('==>', antecedent, conclusion))
            for fact in facts:
                kb.tell(fact)
            closure = set(facts)
            while True:
                expanded = closure | {conclusion for premises, conclusion in rules
                                      if set(premises) <= closure}
                if expanded == closure:
                    break
                closure = expanded
            order = list(atoms)
            rng.shuffle(order)
            for query in order + order[::-1]:
                self.assertEqual(solver.pl_bc_entails(kb, query), query in closure,
                                 (graph, query))


if __name__ == '__main__':
    unittest.main()
