# AGENTS.md — memristec-skill for AI agents

Product root: this directory. Run everything from here with the `memristec`
conda env (`%USERPROFILE%\miniconda3\envs\memristec\python.exe` on Windows,
`conda run -n memristec python` elsewhere; Jupyter kernel `memristec-mc`) and
`PYTHONIOENCODING=utf-8` (Windows consoles are cp1252; the tools print
`—` and `·`).

| Task | Command |
|---|---|
| Health check | `python scripts/verify_memristec.py` |
| Toolkit self-test | `python scripts/memristec_tools.py --selftest` |
| Fast suite | `python -m pytest tests -q` |
| Static check (CI runs it first) | `python -m pyflakes scripts tests build` |
| Cross-check against a local upstream clone | `MEMRISTEC_MODEL_LIBRARY=<clone> python -m pytest tests/test_upstream_crosscheck.py -q` |
| Cross-check CLI with audit log | `MEMRISTEC_MODEL_LIBRARY=<clone> python scripts/upstream_adapter.py` |

The docs guard (`tests/test_docs_guard.py`) fails when a flag below is
missing from this file or from `docs/USER_MANUAL.md`.

## `scripts/memristec_tools.py`

| flag | meaning |
|---|---|
| `--selftest` | run the built-in physics checks and exit |
| `--model {linear_ion_drift,stanford_pku2016,vteam2015,yakopcic2013}` | model to simulate |
| `--window {none,joglekar,biolek,prodromakis}` | window for linear_ion_drift (default joglekar) |
| `--stimulus {rectangular,sin,triangular}` | waveform (default sin) |
| `--amplitude A` | peak voltage in V (default 1.0) |
| `--frequency F` | frequency in Hz (default 1.0) |
| `--cycles N` | number of periods (default 1) |
| `--n-per-cycle N` | grid points per period (default 2000) |
| `--method {euler,rk4,ivp}` | integrator (default rk4) |
| `--outdir DIR` | output directory (default ./out) |
| `--log-dir DIR` | audit-log directory (default <outdir>/logs) |
| `-q`, `--quiet` | print only the verdict |
| `--version` | print `memristec-skill <VERSION>` and exit |

Exit codes: 0 success, 1 a self-test check failed, 2 usage error. A run
writes `<outdir>/<model>_<stimulus>_A<amp>V_F<freq>Hz.csv` (header
`t,v,i,x`) and prints the loop metrics as JSON unless `-q`.

Python entry points (module `memristec_tools`): models `LinearIonDrift(window=...)`,
`Yakopcic2013`, `VTEAM2015`, `StanfordPKU2016` (registry `MODELS`, factory
`make_model(name, **params)`); driver `simulate(model, t, v, method)`;
`iv_sweep(model, amplitude, frequency, cycles, n_per_cycle, stimulus, method)`;
stimuli `sine`, `triangular`, `rectangular`, `pulse_train(t, amplitude, width,
period, n_pulses, t0=0.0, baseline=0.0)`; `pulse_response(model, amplitude,
width, period, n_pulses, read_voltage=0.1, n_per_period=400, method)` ->
`{t, v, x, i, x_after, G_after}`; `loop_metrics(res)` -> `area` (sum of |lobe
areas| over the trajectory), `area_signed`, `i_max`, `i_min`,
`pinched_at_origin`, `r_min`, `r_max`; `dynamic_route_map(model, x_grid,
v_values)`. Equations and parameter provenance: `references/models.md`.

## `scripts/upstream_adapter.py`

| flag | meaning |
|---|---|
| `--library PATH` | path to a local clone (default: $MEMRISTEC_MODEL_LIBRARY) |
| `--model {HP_Biolek2009,Stanford_PKU,VTEAM2015,Yakopcic2013}` | upstream folder to compare (default: all shims) |
| `--outdir DIR` | output directory (default ./out) |
| `--log-dir DIR` | audit-log directory (default <outdir>/logs) |
| `-q`, `--quiet` | print only the verdict |
| `--version` | print `memristec-skill <VERSION>` and exit |

Exit codes: 0 every comparison within tolerance, 1 a comparison exceeded
`tests/records/crosscheck_v1.json`, 2 usage error, 3 no library available.

## `scripts/verify_memristec.py`

| flag | meaning |
|---|---|
| `-q`, `--quiet` | print only the final verdict |
| `--library PATH` | local MemrisTec Model Library clone (default: $MEMRISTEC_MODEL_LIBRARY) |
| `--version` | print `memristec-skill <VERSION>` and exit |

Exit codes: 0 all checks passed, 1 otherwise. Without a library the fifth
check prints `[SKIP] upstream cross-check`.

## `build/assemble.py` and `build/execute.py` — the book

Chapters are generated: edit `build/partNN_*.py`, run assemble then execute;
`tests/test_notebooks.py` compares the committed notebooks with the sources
and their outputs (0 FAIL, captions = figures, ≤ 1 MB). Never edit an `.ipynb`.
`assemble.py` writes every cell with **empty outputs**, and re-assembling
chapter 00 is needed whenever a chapter is added (its list is generated) —
so always execute after assembling, every chapter you re-assembled; a
notebook committed after assemble alone fails `test_committed_notebook_is_green`.
`execute.py --outdir` runs copies elsewhere and passes `MEMRISTEC_SKILL_ROOT`
so the setup cell still finds `scripts/` (that is how `--run-notebooks` works).

| flag | tool | meaning |
|---|---|---|
| `--which KEY` | both | `all` (default), `main`, or one chapter key (`00` … `06`; `--list` shows them) |
| `--outdir DIR` | both | assemble: repository root receiving `chapters/`; execute: write executed copies under `<outdir>/chapters/` instead of in place |
| `--log-dir DIR` | both | audit log directory (default `<outdir>/logs`; `logs/` is gitignored) |
| `--list` | assemble | print chapters, parts, cell and figure counts; write nothing |
| `--indir DIR` | execute | repository root holding `chapters/` (default: this repository) |
| `--kernel NAME` | execute | Jupyter kernel (default `memristec-mc`) |
| `--timeout SEC` | execute | per-cell timeout (default 900) |
| `--tally-only` | execute | do not execute; count PASS/FAIL/figures already stored |
| `-v`, `--verbose` / `-q`, `--quiet` | both | chatty / verdict only |

Exit codes: 0 OK; 1 a FAIL, an error output, an unexecuted cell or an nbconvert
failure; 2 unknown `--which`. `python -m pytest tests --run-notebooks` re-executes
every chapter into a temporary directory (needs the kernel).

## Audit logs

Every `memristec_tools.py` and `upstream_adapter.py` run writes
`<log-dir>/<tool>_<UTC stamp>_<pid>.json` with the keys `tool`, `version`,
`argv`, `utc`, `python`, `platform`, `ok`, and `checks` (a list of
`{name, ok, detail}`) or `results` (per-model `max_abs_dxdt`,
`max_rel_dxdt`, `max_abs_i`, `max_rel_i`, `n`, `max_abs_x`, `max_abs_i`,
`within_tolerance`); a simulation run adds `metrics`, `params`, `csv`.

## Records

`tests/records/crosscheck_v1.json` — `schema: 1`, `generated`, `note`, and
`models.<upstream folder>` (HP_Biolek2009, Yakopcic2013, VTEAM2015, Stanford_PKU) with `max_rel_dxdt`, `max_rel_i` (both tools) and
`max_abs_x_traj` (trajectory test), plus free-text `upstream_window_actual`
/ `finding` annotations. Bump `schema` when a key changes meaning.

## Rules that the suite enforces

- No upstream code in any tracked file; models come from the papers in
  `references/models.md`.
- Every `.py` starts with the SPDX header; README keeps `## Licence` and
  `### Disclaimer`.
- `VERSION`, `CITATION.cff` and `CHANGELOG.md` agree; `SKILL.md` names the
  version and points at existing `references/*.md`.
