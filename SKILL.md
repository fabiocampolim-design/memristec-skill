---
name: memristec
description: Simulate, compare and fit compact memristor models (linear ion drift with Joglekar / Biolek / Prodromakis windows, Yakopcic, and the families of the MemrisTec Model Library) — quasi-static I-V and pinched hysteresis loops, dynamic route maps, pulse responses — and cross-check them against the MemrisTec Model Library. Use this skill whenever the user mentions memristors, memristive devices, RRAM/ReRAM compact models, window functions, pinched hysteresis, MemrisTec, or fitting a memristor model to I-V data — even without naming the library.
license: Apache-2.0
---

# memristec-skill 0.1.0

Clean-room compact memristor models (`references/models.md`), one ODE driver,
I-V sweeps, pinched-loop metrics, dynamic route maps, and an optional
cross-check against a local clone of the MemrisTec Model Library
(`references/platform.md`). Read `references/pitfalls.md` before changing a
grid, a window exponent or a drive amplitude. Run everything from the product
root with the `memristec` conda env and `PYTHONIOENCODING=utf-8`; every flag
is listed in `AGENTS.md`.

## 1. Set up and verify

```bash
scripts/install_memristec_windows.ps1      # or scripts/install_memristec.sh; both accept a dry-run
python scripts/verify_memristec.py         # 4 checks; exit 0 = go
export MEMRISTEC_MODEL_LIBRARY=/path/to/memristec-model-library   # optional: adds the 5th check
python scripts/verify_memristec.py -q      # one-line verdict
```

The environment test and the guards are part of the suite: `python -m pytest
tests -q`.

## 2. Pick a model and simulate

```python
import sys; sys.path.insert(0, "scripts")
import numpy as np
from memristec_tools import make_model, simulate, iv_sweep, STIMULI

m = make_model("linear_ion_drift", window="biolek", R_off=38e3, x0=0.26)   # or "yakopcic2013"
res = iv_sweep(m, amplitude=1.2, frequency=1.0, cycles=2, n_per_cycle=2000, stimulus="sin")
t = np.linspace(0, 2, 4001); v = STIMULI["triangular"](t, 1.0, 1.0)          # any custom drive
res2 = simulate(m, t, v, method="rk4")        # euler | rk4 | ivp; res.t, res.v, res.i, res.x
```

Unknown parameter names raise `ValueError` (typos never silently default).
Parameter sets and their provenance: `references/models.md`.

## 3. I-V and the pinched loop

```python
from memristec_tools import loop_metrics
met = loop_metrics(res)
# area: |loop area| in V·A (0 for a resistor); pinched_at_origin: |i| ~ 0 wherever v ~ 0
# i_max / i_min: extreme currents; r_min / r_max: min / max of v/i away from zero crossings
import matplotlib.pyplot as plt; plt.plot(res.v, res.i); plt.xlabel("V"); plt.ylabel("I")
```

A memristor's loop is pinched at the origin and its area shrinks with
frequency; `area == 0` with `mu_v = 0` is the resistor limit (tested).

## 4. Dynamic route map

```python
from memristec_tools import dynamic_route_map
drm = dynamic_route_map(m, x_grid=np.linspace(0, 1, 101), v_values=[-1.0, -0.5, 0.0, 0.5, 1.0])
for v, dxdt in drm.items(): plt.plot(np.linspace(0, 1, 101), dxdt, label=f"v = {v}")
```

Read the sign: `dx/dt > 0` moves the state to the right (towards `R_on`
for linear ion drift). A window shows as the curve pinching to zero at the
ends; a threshold model (Yakopcic) shows as flat zero for `|v|` below
`Vp`/`Vn`.

## 5. Cross-check against the library

```bash
export MEMRISTEC_MODEL_LIBRARY=/path/to/memristec-model-library
python scripts/upstream_adapter.py                  # every shimmed folder, PASS/FAIL per model, audit log
python scripts/upstream_adapter.py --model HP_Biolek2009 -q
python -m pytest tests/test_upstream_crosscheck.py -q
```

Tolerances and what each comparison means live in
`tests/records/crosscheck_v1.json` (schema 1). The upstream folder
`HP_Biolek2009` is compared with our **Joglekar** variant on purpose: it
implements the Joglekar window (finding P-1 in the study repo's audit);
`references/models.md` records the measured differences.

## Command-line runs and audit logs

`python scripts/memristec_tools.py --model yakopcic2013 --stimulus sin
--amplitude 1 --frequency 1 --cycles 2 --outdir out` writes
`out/<model>_<stimulus>_A<amp>V_F<freq>Hz.csv` (`t,v,i,x`) and a JSON audit
record under `out/logs/`; `--selftest` runs the built-in physics checks.
