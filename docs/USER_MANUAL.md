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
| `--version` | print the version and exit |

Outputs: `<outdir>/<model>_<stimulus>_A<amp>V_F<freq>Hz.csv` with columns
`t,v,i,x` (seconds, volts, amperes, dimensionless state), the loop metrics
printed as JSON (`area`, `i_max`, `i_min`, `pinched_at_origin`, `r_min`,
`r_max`), and an audit record in `<log-dir>`. Exit codes: 0 success, 1 a
self-test check failed, 2 usage error.

## 4. Use the toolkit from Python

```python
import sys; sys.path.insert(0, "scripts")
import numpy as np
from memristec_tools import (make_model, LinearIonDrift, Yakopcic2013, simulate, iv_sweep,
                             loop_metrics, dynamic_route_map, STIMULI)

m = LinearIonDrift(window="joglekar", R_off=16e3, p=10, x0=0.1)
res = iv_sweep(m, amplitude=1.0, frequency=1.0, cycles=1, n_per_cycle=2000, stimulus="sin", method="rk4")
met = loop_metrics(res)                     # dict
drm = dynamic_route_map(m, np.linspace(0, 1, 101), [-1.0, 0.0, 1.0])   # {v: dx/dt over x}
```

- `Model` API: `state_derivative(x, v)`, `current(x, v)`, `params`, `x0`,
  `clip(x)`; `LinearIonDrift` adds `resistance(x)`, `window_value(x, i)`,
  `k`; `Yakopcic2013` adds `g(v)`, `f(x, v)`.
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
| `--model {HP_Biolek2009,Yakopcic2013}` | upstream folder to compare (default: all shims) |
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
python -m pyflakes scripts tests
python -m pytest tests -q
```

The suite covers the environment, the licence and disclaimer wording, the
withheld-material guard, the vendored conformance checker, the physics of
each model, the driver, the metrics, the CLI, the health check, the
cross-check (skipped without a clone) and this documentation (every flag
above is checked against the parsers).
