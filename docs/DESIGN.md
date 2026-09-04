# Design notes — memristec-skill

The decisions behind this repository, what each one cost, and what was rejected.
`README.md` is the product page, `AGENTS.md` the inventory and contract, `SKILL.md` the
agent's entry point; this file is the *why*. Scope, physics targets, the clean-room rule and
every publication decision are the author's; the check-everything methodology was set
jointly; the code, checks, notebooks and drafts were produced by an AI assistant and kept
only after the author's review and a real run.

## 1. The problem framing

The MemrisTec Memristor Model Platform (DFG priority programme SPP 2262) collects compact
memristor models in a Python library that ships without a licence file, without a common
interface and without a package. An AI agent asked to "simulate a memristor with the
MemrisTec models" has nothing verified to stand on: the folders disagree with their own
names (the folder called Biolek implements Joglekar's window), one runner ignores its
voltage argument, another calls an undefined class. This repository is four things sharing
one verified core: an agent skill (`SKILL.md` + `references/`), a toolkit of clean-room
models on one ODE driver (`scripts/memristec_tools.py`), an adapter that runs the *user's
own* clone of the library and compares numbers (`scripts/upstream_adapter.py`), and a book of
executed chapter notebooks in which every physics claim is asserted inline (83 checks, 25
figures in 0.2.0). An undergraduate course follows.

## 2. Decisions and their trade-offs

| Decision | Why | What it costs / what was rejected |
|---|---|---|
| **Clean-room models written from the papers; nothing from the library in the tree.** | The library has no licence, so its code is all-rights-reserved by default and cannot be redistributed. Transcribing the published equation set is both legal and pedagogically the point. | Every model costs a paper read and a parameter check; models without a complete published equation set stay adapter-only (`references/models.md` records the decision per folder). Rejected: vendoring or "cleaning up" upstream code. |
| **An adapter that imports the library at run time from a path the user supplies, plus schema-versioned tolerances.** | Independence has to be measured, not asserted: the cross-check compares our derivative field with theirs on a grid and records the maximum relative difference (2e-16 … 4e-15). It also found the upstream defects (P-1, P-2, P-6). | The shims read attribute names and convert units per folder; a folder rename upstream breaks a shim, which the weekly watch is for. |
| **One state variable `x ∈ [0, 1]`, one fixed-step driver, the state clipped after every stage.** | Every shipped model reduces to `dx/dt = f(x, v)`, `i = g(x, v)`; one driver means one place for numerics and one set of pitfalls. The clip makes a window optional. | Thermal models with a temperature state and the JART model with coupled equations do not fit yet (chapter 6 §25). The clip costs first-order accuracy at a boundary hit (pitfall 4) and the RK4 half-step across a pulse edge integrates 1/6 of a step (pitfall 12). |
| **The notebooks are generated from Python sources** (`build/part*.py`; `build/assemble.py`, `build/execute.py`). | Notebook JSON diffs are unreviewable; sources make every cell a reviewable, testable line, and `chapter_cells(key)` is the single truth the suite compares against. | Editing a notebook directly is forbidden and lost at the next assemble. |
| **Check everything, and report what was measured, not what was expected.** Three plan assumptions died on execution and the chapters say so: self-heating does not move V_set with the teaching parameters (chapter 4, exercise 4.1); identical pulses moved the state by different amounts until `pulse_train` resolved edges consistently (N-8); the VTEAM parameters are not identifiable from a saturating drive (chapter 6, exercise 6.1). | A course that states a result without checking it is indistinguishable from a wrong one. | Checks cost cells and run time; a tightened tolerance can break a chapter. |
| **Chapter notebooks, each under 1 MB, with a TOC and continuous figure numbering.** | Monoliths at several MB crashed editors and sessions elsewhere in the portfolio. | The reader loses the one-file book; `chapters/README.md` (generated) is the index. |
| **Findings ledger with three kinds** (P upstream defect, B proposal, N ours) **and nothing sent by an agent.** | Every upstream contact is drafted in the study repository, verified on a real run and filed by the author under his name; the first item is a licence proposal, because without a licence none of the rest can be used. | Slower than opening an issue from a session; that is the point. |
| **Apache-2.0, `NOTICE` with licence-by-origin, non-affiliation stated.** | Nothing of the platform is vendored; the name identifies what is studied. | — |

## 3. Out of scope (for now)

Circuits (pinned until the upstream circuit simulator ships); the JART VCM and the thermal
threshold-switch families as clean-room models (next, with the fitting workflow for a real
TaO$_x$ device); PyPI packaging (pinned); the course (separate plan).

## 4. Open questions

The paper parameter tables (Yakopcic 2013 Table I, VTEAM Table I, Jiang 2016 Table I) are
still to be checked line by line against the defaults, which are marked "as recalled" or
"ours" until then; a licence upstream (B-1) decides whether the adapter can ever become an
optional dependency instead of a path the user supplies.
