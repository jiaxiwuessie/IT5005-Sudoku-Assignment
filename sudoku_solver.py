"""IT5005 Assignment 1: student implementation file.

Implement the functions marked below. Do not modify utils.py or logic_.py.
"""

from utils import *
from logic_ import *


# Do not change this function; it is used to create atomic propositions.
def atom(prefix, r, c, v):
    """prefix is 'Is' or 'Not'. Returns the Expr for e.g. Is3_2_4."""
    return expr(f'{prefix}{r}_{c}_{v}')


def build_general_kb(n, box_h, box_w, givens):
    """Return a PropKB encoding this n x n Sudoku's constraints plus the given
    cells, as general clauses.

    Parameters
    ----------
    n, box_h, box_w : int
    givens : dict[(int, int), int]

    Returns
    -------
    PropKB
    """
    kb = PropKB()

    # 1. Every cell has at least one value.
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            candidates = [
                atom('Is', r, c, v)
                for v in range(1, n + 1)
            ]
            kb.tell(associate('|', candidates))

    # 2. Every cell has at most one value.
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v1 in range(1, n + 1):
                for v2 in range(v1 + 1, n + 1):
                    kb.tell(
                        ~atom('Is', r, c, v1) | ~atom('Is', r, c, v2)
                    )

    # 3–5. Cells sharing a row, column, or box cannot contain the same value.
    cells = [
        (r, c)
        for r in range(1, n + 1)
        for c in range(1, n + 1)
    ]

    for i, (r1, c1) in enumerate(cells):
        for r2, c2 in cells[i + 1:]:
            same_row = r1 == r2
            same_col = c1 == c2
            same_box = (
                (r1 - 1) // box_h == (r2 - 1) // box_h
                and
                (c1 - 1) // box_w == (c2 - 1) // box_w
            )

            if same_row or same_col or same_box:
                for v in range(1, n + 1):
                    kb.tell(
                        ~atom('Is', r1, c1, v) | ~atom('Is', r2, c2, v)
                    )

    # 6. Add the given values as facts.
    for (r, c), v in givens.items():
        kb.tell(atom('Is', r, c, v))

    return kb


def build_definite_kb(n, box_h, box_w, givens):
    """Return a PropDefiniteKB encoding this n x n Sudoku's constraints plus
    the given cells, using elimination + last-candidate reasoning.

    Parameters
    ----------
    n, box_h, box_w : int
    givens : dict[(int, int), int] -- {(row, col): value}, 1-indexed

    Returns
    -------
    PropDefiniteKB
    """
    dkb = PropDefiniteKB()

    # 1. Infer the last candidate after all other values are excluded.
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                premises = [
                    atom('Not', r, c, other_v)
                    for other_v in range(1, n + 1)
                    if other_v != v
                ]

                dkb.tell(
                    Expr(
                        '==>',
                        associate('&', premises),
                        atom('Is', r, c, v),
                    )
                )

    # 2. A known value excludes all other values in the same cell.
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                conclusions = [
                    atom('Not', r, c, other_v)
                    for other_v in range(1, n + 1)
                    if other_v != v
                ]

                for conclusion in conclusions:
                    dkb.tell(
                        Expr(
                            '==>',
                            atom('Is', r, c, v),
                            conclusion,
                        )
                    )

    # 3–5. Cells sharing a row, column, or box cannot contain the same value.
    cells = [
        (r, c)
        for r in range(1, n + 1)
        for c in range(1, n + 1)
    ]

    for i, (r1, c1) in enumerate(cells):
        for r2, c2 in cells[i + 1:]:
            same_row = r1 == r2
            same_col = c1 == c2
            same_box = (
                (r1 - 1) // box_h == (r2 - 1) // box_h
                and
                (c1 - 1) // box_w == (c2 - 1) // box_w
            )

            if same_row or same_col or same_box:
                for v in range(1, n + 1):
                    dkb.tell(
                        Expr(
                            '==>',
                            atom('Is', r1, c1, v),
                            atom('Not', r2, c2, v),
                        )
                    )

                    dkb.tell(
                        Expr(
                            '==>',
                            atom('Is', r2, c2, v),
                            atom('Not', r1, c1, v),
                        )
                    )

    # 6. Add the given values as facts.
    for (r, c), v in givens.items():
        dkb.tell(atom('Is', r, c, v))

    return dkb


def solve_full_grid_fc(n, box_h, box_w, givens):
    """Solve the whole puzzle using build_definite_kb + pl_fc_entails.

    Returns
    -------
    dict[(int, int), int] -- {(row, col): value} for every cell
    """
    raise NotImplementedError(
        'solve_full_grid_fc: solve every cell with forward chaining'
    )


def pl_bc_entails(kb, query):
    """Your own backward-chaining implementation.

    Parameters
    ----------
    kb : PropDefiniteKB
    query : Expr

    Returns
    -------
    bool
    """
    # Index the KB once.  solve_full_grid_bc asks many queries of the same KB,
    # so repeatedly scanning every clause at every recursive step would be
    # unnecessarily expensive.
    clause_count = len(kb.clauses)
    if getattr(kb, '_bc_index_clause_count', None) != clause_count:
        facts = set()
        rules_by_conclusion = {}

        for clause in kb.clauses:
            premises, conclusion = parse_definite_clause(clause)
            if premises:
                rules_by_conclusion.setdefault(conclusion, []).append(premises)
            else:
                facts.add(conclusion)

        kb._bc_facts = facts
        kb._bc_rules_by_conclusion = rules_by_conclusion
        kb._bc_proven = set(facts)
        kb._bc_query_results = {}
        kb._bc_index_clause_count = clause_count

    # A result cached for a previous top-level query is independent of the
    # current proof path and is therefore safe to reuse.
    if query in kb._bc_query_results:
        return kb._bc_query_results[query]

    # A cycle may make a subgoal fail early in one traversal and become
    # provable later after another rule establishes new facts.  Repeat the
    # recursive search while it is still discovering facts.  The proven set
    # only grows, so this process must reach a fixed point on the finite KB.
    while True:
        proven_before = len(kb._bc_proven)
        active_goals = set()
        failed_this_pass = set()

        def prove(goal):
            """Try to prove one goal by recursively proving rule premises."""
            if goal in kb._bc_proven:
                return True
            if goal in failed_this_pass or goal in active_goals:
                return False

            active_goals.add(goal)
            try:
                # Premises within one rule are combined with AND.  Alternative
                # rules with the same conclusion are combined with OR.
                for premises in kb._bc_rules_by_conclusion.get(goal, []):
                    if all(prove(premise) for premise in premises):
                        kb._bc_proven.add(goal)
                        return True

                failed_this_pass.add(goal)
                return False
            finally:
                active_goals.remove(goal)

        if prove(query):
            result = True
            break
        if len(kb._bc_proven) == proven_before:
            result = False
            break

    kb._bc_query_results[query] = result
    return result


def solve_full_grid_bc(n, box_h, box_w, givens):
    """Solve the whole puzzle using build_definite_kb + your own pl_bc_entails.

    For each cell, try each candidate value until pl_bc_entails confirms one
    -- the same per-cell strategy as solve_full_grid_fc, but backed by
    backward chaining instead of a single shared forward-chaining pass.

    Returns
    -------
    dict[(int, int), int] -- {(row, col): value} for every cell
    """
    kb = build_definite_kb(n, box_h, box_w, givens)
    solved = {}

    for r in range(1, n + 1):
        for c in range(1, n + 1):
            for v in range(1, n + 1):
                if pl_bc_entails(kb, atom('Is', r, c, v)):
                    solved[(r, c)] = v
                    break
            else:
                raise ValueError(
                    f'Backward chaining could not solve cell ({r}, {c})'
                )

    return solved
