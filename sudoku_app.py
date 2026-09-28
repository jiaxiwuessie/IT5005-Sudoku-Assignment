"""Interactive Sudoku tutor. All deduction is delegated to sudoku_solver."""
import json
from html import escape
from pathlib import Path
from time import perf_counter
import streamlit as st
from sudoku_solver import (
    atom, build_definite_kb, build_general_kb, solve_full_grid_fc,
    solve_full_grid_bc, pl_bc_entails, trace_fc_query,
)


def load_puzzles(path):
    """Expose only givens to the app; reference solutions are never retained."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    puzzles = [{tuple(map(int, key.split("_"))): value
                for key, value in p["givens"].items()} for p in raw["puzzles"]]
    return raw["n"], raw["box_h"], raw["box_w"], puzzles


def parse_atom(proposition):
    name = proposition.op
    prefix = "Not" if name.startswith("Not") else "Is"
    if not name.startswith(prefix):
        raise ValueError(f"Unsupported Sudoku proposition: {name}")
    return (prefix, *map(int, name[len(prefix):].split("_")))


def describe_atom(proposition):
    prefix, r, c, value = parse_atom(proposition)
    return f"R{r}C{c} {'is' if prefix == 'Is' else 'cannot be'} {value}"


def explain_step(step, box_h, box_w):
    """Translate an observed rule application, never infer new facts here."""
    prefix, r, c, value = parse_atom(step["conclusion"])
    premises = step["premises"]
    if step["rule"] is None:
        return "Given", f"The puzzle gives {describe_atom(step['conclusion'])}."
    if prefix == "Is":
        values = ", ".join(map(str, sorted(parse_atom(p)[3] for p in premises)))
        return "Last candidate", (f"R{r}C{c} cannot contain {values}. Every other value "
                                   f"has been excluded, so its last remaining candidate is {value}.")
    _, source_r, source_c, source_value = parse_atom(premises[0])
    if (r, c) == (source_r, source_c):
        return "One value per cell", (f"R{r}C{c} is already {source_value}. A cell holds "
                                      f"one value, so it cannot also be {value}.")
    if r == source_r:
        kind, unit = "Row exclusion", f"row {r}"
    elif c == source_c:
        kind, unit = "Column exclusion", f"column {c}"
    else:
        kind = "Box exclusion"
        top, left = ((r - 1) // box_h) * box_h + 1, ((c - 1) // box_w) * box_w + 1
        unit = f"box spanning rows {top}–{top + box_h - 1} and columns {left}–{left + box_w - 1}"
    return kind, (f"R{source_r}C{source_c} contains {source_value} in the same {unit}. "
                  f"A digit cannot repeat there, so R{r}C{c} cannot be {value}.")


def valid_grid(grid, n, box_h, box_w, givens):
    """Check Sudoku constraints without consulting a reference answer."""
    expected = set(range(1, n + 1))
    if set(grid) != {(r, c) for r in expected for c in expected}:
        return False
    units = [[(r, c) for c in range(1, n + 1)] for r in range(1, n + 1)]
    units += [[(r, c) for r in range(1, n + 1)] for c in range(1, n + 1)]
    units += [[(r, c) for r in range(top, top + box_h) for c in range(left, left + box_w)]
              for top in range(1, n + 1, box_h) for left in range(1, n + 1, box_w)]
    return (all({grid[cell] for cell in unit} == expected for unit in units)
            and all(grid.get(cell) == value for cell, value in givens.items()))


def board_html(n, box_h, box_w, givens, values=None, focus=None,
               premises=(), eliminated=None, label="Sudoku board"):
    values = givens if values is None else values
    cells = ['<thead><tr><th aria-label="Row / column"></th>']
    cells.extend(f'<th scope="col">{c}</th>' for c in range(1, n + 1))
    cells.append('</tr></thead><tbody>')
    for r in range(1, n + 1):
        cells.append(f'<tr><th scope="row">{r}</th>')
        for c in range(1, n + 1):
            cell, value = (r, c), values.get((r, c))
            classes = ["given" if cell in givens else "deduced"]
            if c % box_w == 0 and c < n: classes.append("box-right")
            if r % box_h == 0 and r < n: classes.append("box-bottom")
            if cell in premises: classes.append("premise")
            if cell == focus: classes.append("focus-cell")
            body = str(value) if value is not None else "&middot;"
            state = "given" if cell in givens else "deduced" if value else "empty"
            desc = f"Row {r}, column {c}: {value or 'empty'}, {state}"
            if cell == focus and eliminated is not None:
                body += f'<small>≠{eliminated}</small>'
                desc += f", excluded value {eliminated}"
            cells.append(f'<td class="{" ".join(classes)}" aria-label="{escape(desc)}">{body}</td>')
        cells.append('</tr>')
    cells.append('</tbody>')
    return (f'<div class="board-wrap"><table class="sudoku-board" '
            f'aria-label="{escape(label)}">{"".join(cells)}</table></div>')


def proof_text(steps, box_h, box_w):
    lines = ["Forward-chaining supporting proof", ""]
    for i, step in enumerate(steps, 1):
        kind, explanation = explain_step(step, box_h, box_w)
        lines.append(f"{i}. [{kind}] {explanation}")
        lines.append("   Premises: " + ("; ".join(describe_atom(p) for p in step["premises"]) or "Puzzle given"))
        lines.append("   Conclusion: " + describe_atom(step["conclusion"]))
    return "\n".join(lines)


CSS = """
<style>
.stApp { background: #f7f8f5; }
.block-container { max-width: 1160px; padding-top: 2.4rem; }
h1, h2, h3 { color: #162e39; }
.eyebrow { color: #167468; letter-spacing: .15em; font-size: .75rem; font-weight: 750; margin-bottom: .7rem; }
.intro { color: #57676b; font-size: 1.04rem; max-width: 710px; margin-bottom: 1.6rem; }
.board-wrap { max-width: 500px; margin: .4rem auto 1rem; }
.sudoku-board { border-collapse: separate; border-spacing: 0; width: 100%; table-layout: fixed; color: #16323d; }
.sudoku-board th { font: 500 .72rem sans-serif; color: #677c83; height: 25px; text-align: center; border: 0; }
.sudoku-board th:first-child { width: 25px; }
.sudoku-board td { position: relative; text-align: center; height: 47px; padding: 0;
 border-right: 1px solid #d7e1df; border-bottom: 1px solid #d7e1df;
 font: 500 1.27rem ui-monospace, SFMono-Regular, Menlo, monospace; background: #fff; }
.sudoku-board tr:first-child td { border-top: 2px solid #597477; }
.sudoku-board td:nth-child(2) { border-left: 2px solid #597477; }
.sudoku-board tr:last-child td { border-bottom: 2px solid #597477; }
.sudoku-board td:last-child { border-right: 2px solid #597477; }
.sudoku-board td.box-right { border-right: 2px solid #597477; }
.sudoku-board td.box-bottom { border-bottom: 2px solid #597477; }
.sudoku-board td.given { background: #edf2f0; font-weight: 800; color: #1d3640; }
.sudoku-board td.deduced { color: #127567; }
.sudoku-board td.premise { background: #e4eefc; }
.sudoku-board td.focus-cell { background: #fff0c5; box-shadow: inset 0 0 0 2px #ad7b1a; }
.sudoku-board td small { position: absolute; bottom: 1px; right: 3px; color: #9b3c27; font: 10px sans-serif; }
.legend { color: #637578; font-size: .8rem; margin-bottom: 1rem; text-align: center; }
.proof-kind { color: #167468; font-size: .82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }
@media (max-width: 600px) {
 .block-container { padding-top: 1.5rem; }
 .sudoku-board td { height: 35px; font-size: 1.05rem; }
 .sudoku-board th:first-child { width: 20px; }
}
</style>
"""


def render_proof(result, n, box_h, box_w, givens):
    steps = result["steps"]
    if not steps: return
    st.divider()
    st.subheader("Follow the proof")
    st.caption("A forward-chaining supporting proof for the query above. The verdict was computed "
               "by backward chaining and independently checked by forward chaining. "
               "This is not the backward search log.")
    count = len(steps)
    query_key = "_".join(map(str, result["query"]))
    if count > 1:
        position = st.slider("Proof step", 1, count, count,
                             key=f"proof_{result['puzzle']}_{query_key}_{result['run']}")
    else:
        position = 1
        st.caption("This query is an initial given: one fact is sufficient.")
    step = steps[position - 1]
    prefix, r, c, value = parse_atom(step["conclusion"])
    state = dict(givens)
    for item in steps[:position]:
        p, row, col, val = parse_atom(item["conclusion"])
        if p == "Is": state[(row, col)] = val
    premise_cells = [parse_atom(p)[1:3] for p in step["premises"]]
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(board_html(n, box_h, box_w, givens, state, (r, c), premise_cells,
                              value if prefix == "Not" else None, "Proof replay board"), unsafe_allow_html=True)
        st.markdown('<div class="legend">Gold: current conclusion · Blue: premise cells</div>', unsafe_allow_html=True)
    with right:
        kind, explanation = explain_step(step, box_h, box_w)
        st.markdown(f'<p class="proof-kind">Step {position} of {count} · {escape(kind)}</p>', unsafe_allow_html=True)
        st.markdown(f"### {describe_atom(step['conclusion'])}")
        st.write(explanation)
        with st.expander("Evidence for this step", expanded=True):
            if step["premises"]:
                for premise in step["premises"]: st.write("• " + describe_atom(premise))
            else:
                st.write("This fact is supplied by the puzzle.")
        st.caption("Replay shows only the facts needed for this proof, not a separate full-grid solve. "
                   "When cells share several constraints, one valid shared unit is used in the explanation.")
    with st.expander(f"Read the complete proof ({count} steps)"):
        with st.container(height=320):
            for i, item in enumerate(steps, 1):
                kind, explanation = explain_step(item, box_h, box_w)
                st.markdown(f"**{i}. {kind}** — {explanation}")
    st.download_button("Download proof", proof_text(steps, box_h, box_w),
                       file_name=f"puzzle_{result['puzzle'] + 1}_proof_{query_key}.txt", mime="text/plain")


def main():
    st.set_page_config(page_title="Sudoku Logic Lab", page_icon="🧩", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    try:
        n, box_h, box_w, puzzles = load_puzzles(Path(__file__).with_name("puzzles.json"))
    except (OSError, ValueError, KeyError) as error:
        st.error(f"Could not load the puzzle pool: {error}")
        st.stop()
    with st.sidebar:
        st.markdown("### Puzzle library")
        selected = st.selectbox("Choose a puzzle", range(len(puzzles)),
                                format_func=lambda i: f"Puzzle {i + 1} · {len(puzzles[i])} givens", key="puzzle_selection")
        givens = puzzles[selected]
        st.caption(f"{n} × {n} board · {box_h} × {box_w} boxes")
        st.metric("Starting clues", len(givens))
        st.caption(f"{n * n - len(givens)} cells to deduce")
        if st.button("Reset this puzzle", use_container_width=True):
            for key in ("solve_result", "query_result"): st.session_state.pop(key, None)
        st.divider()
        st.markdown("**How to explore**")
        st.write("1. Pick a puzzle.\n2. Choose an algorithm and solve.\n3. Ask about a cell.\n4. Follow the evidence step by step.")
        with st.expander("About the algorithms"):
            st.write("Forward chaining starts from known facts and fires rules. Backward chaining starts "
                     "from a target and tries to prove the premises of rules that support it.")
            st.write("Both use the same elimination and last-candidate rules. These rules need not solve every possible Sudoku.")
        st.caption("IT5005 · Knowledge representation & inference")
    if st.session_state.get("active_puzzle") != selected:
        for key in ("solve_result", "query_result"): st.session_state.pop(key, None)
        st.session_state["active_puzzle"] = selected
    st.markdown('<div class="eyebrow">IT5005 / INTERACTIVE LOGIC TUTOR</div>', unsafe_allow_html=True)
    st.title("Sudoku Logic Lab")
    st.markdown('<div class="intro">From a given number to a justified conclusion. Solve a puzzle, '
                'ask a precise question, and see the rules behind the answer.</div>', unsafe_allow_html=True)
    board_column, control_column = st.columns([1.1, 1], gap="large")
    with control_column:
        st.subheader("Solve the whole board")
        algorithm = st.radio("Inference algorithm", ["Forward chaining", "Backward chaining"], horizontal=True, key="algorithm")
        if st.button("Solve puzzle", type="primary", use_container_width=True):
            st.session_state.pop("solve_result", None)
            try:
                with st.spinner(f"Solving with {algorithm.lower()}…"):
                    started = perf_counter()
                    solver = solve_full_grid_fc if algorithm == "Forward chaining" else solve_full_grid_bc
                    solved = solver(n, box_h, box_w, givens)
                    elapsed = perf_counter() - started
                    if not valid_grid(solved, n, box_h, box_w, givens):
                        raise ValueError("The returned grid does not satisfy the Sudoku constraints.")
                st.session_state["solve_result"] = {"grid": solved, "seconds": elapsed, "algorithm": algorithm, "puzzle": selected}
            except (ValueError, RecursionError) as error:
                st.error(f"Could not complete this puzzle: {error}")
        solved_result = st.session_state.get("solve_result")
        if solved_result:
            st.success(f"Solved with {solved_result['algorithm'].lower()} · {solved_result['seconds']:.3f} s")
            st.caption("Time includes a fresh knowledge base, indexing, inference and grid reconstruction. "
                       "Validation and rendering are excluded. Each click runs again.")
        st.divider()
        st.subheader("Ask about a cell")
        st.caption("Is this value logically implied by the puzzle? Rows and columns start at 1.")
        with st.form("cell_query"):
            a, b, c = st.columns(3)
            row = a.number_input("Row", min_value=1, max_value=n, value=1, step=1, key="query_row")
            col = b.number_input("Column", min_value=1, max_value=n, value=1, step=1, key="query_col")
            value = c.number_input("Value", min_value=1, max_value=n, value=1, step=1, key="query_value")
            submitted = st.form_submit_button("Check entailment", use_container_width=True)
        if submitted:
            st.session_state.pop("query_result", None)
            try:
                with st.spinner("Checking the query and collecting its supporting proof…"):
                    kb = build_definite_kb(n, box_h, box_w, givens)
                    query = atom("Is", row, col, value)
                    started = perf_counter()
                    verdict = pl_bc_entails(kb, query)
                    query_seconds = perf_counter() - started
                    fc_verdict, steps = trace_fc_query(kb, query)
                    if verdict != fc_verdict:
                        raise ValueError("The two inference engines disagree; no proof is displayed.")
                run = st.session_state.get("query_run", 0) + 1
                st.session_state["query_run"] = run
                st.session_state["query_result"] = {"verdict": bool(verdict), "steps": steps,
                    "query": (row, col, value), "seconds": query_seconds, "puzzle": selected, "run": run}
            except (ValueError, RecursionError) as error:
                st.error(f"Could not answer this query: {error}")
        result = st.session_state.get("query_result")
        if result:
            r, c, v = result["query"]
            label = f"{'True' if result['verdict'] else 'False'} · Is R{r}C{c} = {v}?"
            if result["verdict"]:
                st.success(label)
                st.caption("The knowledge base entails this value. Explore its proof below.")
            else:
                st.info(label)
                st.caption("This value was not proved by the knowledge base. False is not, by itself, "
                           "a proof of the opposite. There is no successful proof to replay.")
            st.caption(f"Backward-chaining query: {result['seconds']:.3f} s "
                       "(includes BC indexing; excludes knowledge-base construction and FC explanation).")
    with board_column:
        solved_result = st.session_state.get("solve_result")
        st.subheader(f"Puzzle {selected + 1}" + (" · solved" if solved_result else " · starting grid"))
        query_result = st.session_state.get("query_result")
        focus = query_result["query"][:2] if query_result else None
        st.markdown(board_html(n, box_h, box_w, givens, solved_result["grid"] if solved_result else None, focus), unsafe_allow_html=True)
        st.markdown('<div class="legend">Bold on gray: givens · Green: deduced · Gold: queried cell</div>', unsafe_allow_html=True)
        st.caption("All rows, columns and boxes validated. Initial clues are preserved." if solved_result
                   else "Every answer is derived from the initial clues and the encoded rules.")
    result = st.session_state.get("query_result")
    if result and result["verdict"]: render_proof(result, n, box_h, box_w, givens)


if __name__ == "__main__":
    main()
