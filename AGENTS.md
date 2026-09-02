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
| Static check (CI runs it first) | `python -m pyflakes scripts tests` |
| Cross-check against a local upstream clone | `MEMRISTEC_MODEL_LIBRARY=<clone> python -m pytest tests/test_upstream_crosscheck.py -q` |
| Cross-check CLI with audit log | `MEMRISTEC_MODEL_LIBRARY=<clone> python scripts/upstream_adapter.py` |

The docs guard (`tests/test_docs_guard.py`) fails when a flag below is
missing from this file or from `docs/USER_MANUAL.md`.

## `scripts/memristec_tools.py`

| flag | meaning |
|---|---|
| `--selftest` | run the built-in physics checks and exit |
| `--model {linear_ion_drift,yakopcic2013}` | model to simulate |
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

## `scripts/upstream_adapter.py`

| flag | meaning |
|---|---|
| `--library PATH` | path to a local clone (default: $MEMRISTEC_MODEL_LIBRARY) |
| `--model {HP_Biolek2009,Yakopcic2013}` | upstream folder to compare (default: all shims) |
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

## Audit logs

Every `memristec_tools.py` and `upstream_adapter.py` run writes
`<log-dir>/<tool>_<UTC stamp>_<pid>.json` with the keys `tool`, `version`,
`argv`, `utc`, `python`, `platform`, `ok`, and `checks` (a list of
`{name, ok, detail}`) or `results` (per-model `max_abs_dxdt`,
`max_rel_dxdt`, `max_abs_i`, `max_rel_i`, `n`, `max_abs_x`, `max_abs_i`,
`within_tolerance`); a simulation run adds `metrics`, `params`, `csv`.

## Records

`tests/records/crosscheck_v1.json` — `schema: 1`, `generated`, `note`, and
`models.<upstream folder>` with `max_rel_dxdt`, `max_rel_i` (both tools) and
`max_abs_x_traj` (trajectory test), plus free-text `upstream_window_actual`
/ `finding` annotations. Bump `schema` when a key changes meaning.

## Rules that the suite enforces

- No upstream code in any tracked file; models come from the papers in
  `references/models.md`.
- Every `.py` starts with the SPDX header; README keeps `## Licence` and
  `### Disclaimer`.
- `VERSION`, `CITATION.cff` and `CHANGELOG.md` agree; `SKILL.md` names the
  version and points at existing `references/*.md`.
