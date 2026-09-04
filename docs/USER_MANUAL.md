# memristec-skill — user manual

Version: see `VERSION` (every script prints it with `--version`).

## 1. Install

Windows (PowerShell):

```powershell
scripts\install_memristec_windows.ps1 -DryRun     # prints the three steps, runs nothing
scripts\install_memristec_windows.ps1             # creates conda env `memristec`, kernel `memristec-mc`
```

Linux / macOS:

```bash
bash scripts/install_memristec.sh --dry-run
bash scripts/install_memristec.sh [--conda /path/to/conda]
```

Both print one `<step> : OK | FAIL | DRY-RUN` line per step and exit 1 on
the first failure. Without conda: `python -m pip install -r
requirements.txt` (Python ≥ 3.12).

Environment facts: the interpreter is
`%USERPROFILE%\miniconda3\envs\memristec\python.exe` on Windows and `conda
run -n memristec python` elsewhere; the Jupyter kernel is `memristec-mc`;
Windows consoles are cp1252, so set `PYTHONIOENCODING=utf-8` before running
any tool.

## 2. Verify

```bash
python scripts/verify_memristec.py            # [PASS]/[FAIL] per check, then the verdict; exit 0/1
python scripts/verify_memristec.py -q         # verdict only
python scripts/verify_memristec.py --library /path/to/memristec-model-library
```

| flag | meaning |
|---|---|
| `-q`, `--quiet` | print only the final verdict |
| `--library PATH` | local MemrisTec Model Library clone (default: `$MEMRISTEC_MODEL_LIBRARY`) |
| `--version` | print the version and exit |

Checks: imports and versions; linear ion drift with the Biolek window gives a
pinched loop of positive area; memristance is affine in charge without a
window (Strukov 2008 eq. 6); Yakopcic 2013 has no motion below threshold
and switches under 1 V; upstream cross-check of Yakopcic2013 when a clone is
available (`[SKIP]` otherwise).

## 3. Simulate from the command line

```bash
python scripts/memristec_tools.py --selftest
python scripts/memristec_tools.py --model linear_ion_drift --window biolek --stimulus sin \
       --amplitude 1.2 --frequency 1 --cycles 2 --n-per-cycle 2000 --method rk4 --outdir out
python scripts/memristec_tools.py --model yakopcic2013 --stimulus triangular -q
```

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
| `--version` | print the version and exit |

Outputs: `<outdir>/<model>_<stimulus>_A<amp>V_F<freq>Hz.csv` with columns
`t,v,i,x` (seconds, volts, amperes, dimensionless state), the loop metrics
printed as JSON (`area` — the sum of the |lobe areas| over the whole
trajectory —, `area_signed`, `i_max`, `i_min`, `pinched_at_origin`, `r_min`,
`r_max`), and an audit record in `<log-dir>`. Exit codes: 0 success, 1 a
self-test check failed, 2 usage error.

## 4. Use the toolkit from Python

```python
import sys; sys.path.insert(0, "scripts")
import numpy as np
from memristec_tools import (make_model, LinearIonDrift, Yakopcic2013, VTEAM2015, StanfordPKU2016,
                             simulate, iv_sweep, loop_metrics, dynamic_route_map, STIMULI,
                             pulse_train, pulse_response)

m = LinearIonDrift(window="joglekar", R_off=16e3, p=10, x0=0.1)
res = iv_sweep(m, amplitude=1.0, frequency=1.0, cycles=1, n_per_cycle=2000, stimulus="sin", method="rk4")
met = loop_metrics(res)                     # dict
drm = dynamic_route_map(m, np.linspace(0, 1, 101), [-1.0, 0.0, 1.0])   # {v: dx/dt over x}

# pulse programming (chapter 5): 20 potentiating pulses, conductance read at 0.1 V after each
ltp = pulse_response(VTEAM2015(x0=0.8), -0.5, width=0.02, period=0.05, n_pulses=20)
print(ltp["x_after"][:3], ltp["G_after"][:3])       # VTEAM potentiates with pulses below v_on
t = np.linspace(0, 1, 20001); v = pulse_train(t, 0.9, width=1e-2, period=5e-2, n_pulses=10)
snap = simulate(StanfordPKU2016(), t, v)              # any train through the driver
```

- `Model` API: `state_derivative(x, v)`, `current(x, v)`, `params`, `x0`,
  `clip(x)`; `LinearIonDrift` adds `resistance(x)`, `window_value(x, i)`,
  `k`; `Yakopcic2013` adds `g(v)`, `f(x, v)`; `VTEAM2015` adds `resistance(x)`,
  `window_value(x)` (x = 0 is R_on — the paper's convention); `StanfordPKU2016`
  adds `gap(x)`, `temperature(x, v)`, `gamma(x)`, `gap_rate(x, v)` (x = 1 is
  the smallest gap; stiff: use 20 000 points per period).
- `pulse_response` returns `x_after[k]` / `G_after[k]`, the state and the read
  conductance after pulse k; `loop_metrics["area"]` sums the |lobe areas| over
  the whole trajectory (divide by `cycles` for the area per period).
- `simulate(model, t, v, method)` integrates on your grid and returns
  `SimResult(t, v, i, x)`; `method` is `euler`, `rk4` (default) or `ivp`.
- Stimuli: `STIMULI["sin"|"triangular"|"rectangular"](t, amplitude,
  frequency[, duty])`; the triangle starts at `−A` like the upstream
  function generator.
- Equations, citations and default parameters: `references/models.md`;
  numerical traps: `references/pitfalls.md`.

## 5. Cross-check against the MemrisTec Model Library

Clone the library yourself (it has no licence file, so it is never shipped
here; a partial clone is enough, see `references/platform.md`) and point
the tools at it:

```bash
export MEMRISTEC_MODEL_LIBRARY=/path/to/memristec-model-library
python scripts/upstream_adapter.py                       # all shimmed folders
python scripts/upstream_adapter.py --model Yakopcic2013 --outdir out --log-dir out/logs -q
python -m pytest tests/test_upstream_crosscheck.py -q
```

| flag | meaning |
|---|---|
| `--library PATH` | path to a local clone (default: `$MEMRISTEC_MODEL_LIBRARY`) |
| `--model {HP_Biolek2009,Stanford_PKU,VTEAM2015,Yakopcic2013}` | upstream folder to compare (default: all shims) |
| `--outdir DIR` | output directory (default ./out) |
| `--log-dir DIR` | audit-log directory (default <outdir>/logs) |
| `-q`, `--quiet` | print only the verdict |
| `--version` | print the version and exit |

Exit codes: 0 within tolerance, 1 a comparison exceeded the records, 2 usage
error, 3 no library available. Tolerances are in
`tests/records/crosscheck_v1.json` (`schema: 1`; per upstream folder
`max_rel_dxdt`, `max_rel_i`, and `max_abs_x_traj` for the trajectory
test). Why `HP_Biolek2009` is compared with our Joglekar variant:
`references/models.md`.

## 6. Audit logs

Every `memristec_tools.py` and `upstream_adapter.py` run writes
`<log-dir>/<tool>_<UTC stamp>_<pid>.json` with `tool`, `version`, `argv`,
`utc`, `python`, `platform`, `ok`, and either `checks` (`{name, ok,
detail}` list) or `results` (per-model differences and
`within_tolerance`); simulation runs add `metrics`, `params`, `csv`. Keep
them with your results — they say which version produced which file.

## 7. Tests

```bash
python -m pyflakes scripts tests build
python -m pytest tests -q
```

The suite covers the environment, the licence and disclaimer wording, the
withheld-material guard, the vendored conformance checker, the physics of
each model, the driver, the metrics, the CLI, the health check, the
cross-check (skipped without a clone) and this documentation (every flag
above is checked against the parsers).

## 8. The book (`chapters/`)

Six executed chapter notebooks, one per subject, indexed by
`chapters/README.md`. They are **generated**: the sources are the cell lists
in `build/partNN_*.py`; `build/assemble.py` writes the notebooks (header with
table of contents and navigation, the shared setup cell, the chapter's cells,
a tally cell) and `build/execute.py` runs them on the `memristec-mc` kernel,
stores the outputs in place and counts the inline `[PASS]`/`[FAIL]` checks.
Never edit an `.ipynb` by hand — `tests/test_notebooks.py` compares every
committed notebook with the sources.

```bash
python build/assemble.py --list            # chapters, parts, cell and figure counts
python build/assemble.py                   # write every chapter + chapters/README.md
python build/execute.py -v                 # execute all, in place; logs/execute.log
python build/execute.py --which 03         # one chapter
python -m pytest tests --run-notebooks     # re-execute every chapter into a temp dir (slow)
```

| flag | tool | meaning |
|---|---|---|
| `--which KEY` | both | `all` (default), `main`, or one chapter key (`00` … `06`) |
| `--outdir DIR` | both | assemble: repository root receiving `chapters/`; execute: executed copies under `<outdir>/chapters/` |
| `--log-dir DIR` | both | audit log directory (default `<outdir>/logs`) |
| `--list` | assemble | list only, write nothing |
| `--indir DIR` | execute | repository root holding `chapters/` |
| `--kernel NAME` | execute | Jupyter kernel (default `memristec-mc`) |
| `--timeout SEC` | execute | per-cell timeout (default 900) |
| `--tally-only` | execute | count what is already stored, do not execute |
| `-v`, `--verbose` / `-q`, `--quiet` | both | chatty / verdict only |

Exit codes: 0 OK; 1 a FAIL, an error output, an unexecuted cell or an
nbconvert failure; 2 unknown `--which`. Every run appends to
`logs/assemble.log` or `logs/execute.log` (gitignored). Chapter 6 §24 needs
`MEMRISTEC_MODEL_LIBRARY` for its cross-check cell and prints `[SKIP]` otherwise.

## 8a. This manual as HTML or PDF

```bash
python docs/build_manual.py                 # docs/USER_MANUAL.html (+ .pdf with pandoc and xelatex/lualatex)
python docs/build_manual.py --outdir out/ --no-pdf -v
```

| flag | meaning |
|---|---|
| `--outdir DIR` | where `USER_MANUAL.html` / `.pdf` go (default `docs/`) |
| `--no-pdf` | write the HTML only |
| `-v`, `--verbose` | print the converter used and the commands |

Without pandoc a built-in converter writes the HTML and the PDF is skipped with
a notice; exit 1 when pandoc or the PDF engine fails.

## 9. Watch the upstream library weekly

The MemrisTec GitLab sits behind a bot wall, so the watch works on your local
clone: it fetches, records every remote branch head, the tags and the tree
hash of every `models/<folder>` on every branch, compares with the previous
run and writes a dated report. Only tree-level git commands are used, so a
partial clone (`--filter=blob:none`) never downloads blobs.

```bash
export MEMRISTEC_MODEL_LIBRARY=/path/to/memristec-model-library
python scripts/watch_upstream.py --weekly                    # report in ../docs/watch/YYYY-WW.md
python scripts/watch_upstream.py --weekly --no-fetch -q      # offline comparison
python scripts/watch_upstream.py --snapshot --state-dir /tmp/state --clone /path/to/clone
powershell -File scripts/register_watch_task.ps1 -DryRun     # Windows: weekly task, Mondays 08:00
```

| flag | meaning |
|---|---|
| `--weekly` | fetch, compare with the previous snapshot, write the report, then snapshot |
| `--snapshot` | record the current state only |
| `--no-fetch` | do not `git fetch`; compare the clone as it is |
| `--clone PATH` | local clone of the library (default: `$MEMRISTEC_MODEL_LIBRARY`) |
| `--state-dir DIR` | snapshot and logs (default `<study>/forum/upstream-watch`) |
| `--outdir DIR` | weekly reports (default `<study>/docs/watch`) |
| `--log-dir DIR` | audit-log directory (default `<state-dir>/logs`) |
| `-q`, `--quiet` | print only the verdict |
| `--version` | print the version and exit |

Exit codes: 0 OK, 1 git failed, 2 no mode given, 3 no clone available. The
first run reports every branch as new; from the second run on it lists moved
branches, added / removed / changed model folders and the new commits (one
line each, no diffs).
