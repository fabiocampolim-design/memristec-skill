---
name: memristec
description: Simulate, compare and fit compact memristor models (linear ion drift with Joglekar / Biolek / Prodromakis windows, Yakopcic 2013, VTEAM 2015, the Stanford–PKU filamentary model, and the families of the MemrisTec Model Library) — quasi-static I-V and pinched hysteresis loops, dynamic route maps, pulse programming (potentiation / depression / read disturb), least-squares fits — and cross-check them against the MemrisTec Model Library. Use this skill whenever the user mentions memristors, memristive devices, RRAM/ReRAM compact models, window functions, pinched hysteresis, threshold switching, MemrisTec, neuromorphic crossbars, or fitting a memristor model to I-V data — even without naming the library.
license: Apache-2.0
---

# memristec-skill 0.2.5

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

m = make_model("linear_ion_drift", window="biolek", R_off=38e3, x0=0.26)   # or "yakopcic2013", "vteam2015", "stanford_pku2016"
res = iv_sweep(m, amplitude=1.2, frequency=1.0, cycles=2, n_per_cycle=2000, stimulus="sin")
t = np.linspace(0, 2, 4001); v = STIMULI["triangular"](t, 1.0, 1.0)          # any custom drive
res2 = simulate(m, t, v, method="rk4")        # euler | rk4 | ivp; res.t, res.v, res.i, res.x
```

Unknown parameter names raise `ValueError` (typos never silently default).
Parameter sets and their provenance: `references/models.md`. Which model fits
which device class (VCM / ECM / thermal threshold / area-dependent, volatile
or not, filamentary or not) and which data set: `references/taxonomy.md`.

## 3. I-V and the pinched loop

```python
from memristec_tools import loop_metrics
met = loop_metrics(res)
# area: sum of the |lobe areas| in V·A over the whole trajectory (divide by `cycles` for the area
#       per period; 0 for a resistor); area_signed: the signed shoelace value (cancels for a
#       symmetric pinched loop); pinched_at_origin: |i| ~ 0 wherever v ~ 0
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

## 6. Fit a model to a measurement (synthetic now, the TaOx device later)

Least squares on the current: simulate with trial parameters, subtract the data, let scipy
adjust. Chapter 6 §23 of the book is the reference cell. Check identifiability first: a drive
that saturates the device for every parameter set carries no information about the rate
(chapter 6, exercise 6.1) — use an amplitude at which the device switches only partially.

```python
from scipy.optimize import least_squares
from memristec_tools import VTEAM2015, iv_sweep
data = iv_sweep(VTEAM2015(k_off=25.0, v_off=0.35), 0.5, 1.0, cycles=1, n_per_cycle=2000)   # stand-in for a measurement
scale = abs(data.i).max()
res = lambda p: (iv_sweep(VTEAM2015(k_off=p[0], v_off=p[1]), 0.5, 1.0, cycles=1, n_per_cycle=2000).i - data.i) / scale
sol = least_squares(res, [10.0, 0.3], bounds=([0.1, 0.05], [200, 0.7]), diff_step=1e-3)
print(sol.x)                                   # → [25.0, 0.35]
```

## 7. Pulse programming: potentiation, depression, read disturb

`pulse_response` applies a train of identical pulses and reads the conductance after each one
(chapter 5). Mind the signs: VTEAM potentiates with pulses *below* `v_on` (negative); the
linear-drift, Yakopcic and Stanford–PKU models with positive pulses. Reads inside the dead band
of a threshold model cost nothing; reads of a linear-drift model always write a little. Pulse
edges on the grid integrate 1/6 of a step each (`references/pitfalls.md` 12): compare pulses
from the second one on and quote per-pulse steps to 1 %.

```python
from memristec_tools import VTEAM2015, StanfordPKU2016, pulse_response
ltp = pulse_response(VTEAM2015(x0=0.8), -0.5, width=0.02, period=0.05, n_pulses=20)   # G_after rises
ltd = pulse_response(VTEAM2015(x0=0.0), +0.5, width=0.02, period=0.05, n_pulses=20)   # G_after falls
snap = pulse_response(StanfordPKU2016(), 0.9, width=1e-5, period=2e-5, n_pulses=20)   # gradual, then abrupt
print(ltp["G_after"][[0, 9, 19]], snap["x_after"][[0, 9, 19]])
```

## 8. Hand-off to neuromorphic frameworks

aihwkit and snnTorch need a conductance-update table and a read model, not an ODE: build the
table from `pulse_response` (one entry per pulse count) and read with `G @ v` (chapter 5 §20).
Nothing from the MemrisTec library is needed for this; its models would need a licence (B-1)
before a framework could import them.

## 9. Pitfalls and where compact models stop

Read `references/pitfalls.md` before changing a grid or an amplitude: the Stanford–PKU model is
stiff (20 000 points per period, RK4), VTEAM's state runs the other way (x = 0 is R_on), the
loop area is the sum of the lobes over the whole trajectory. The shipped models have no
relaxation term (no retention loss, no volatility); thermal and data-driven models of the
library are adapter-only (chapter 6 §25).

## The book

`chapters/README.md` indexes six executed chapter notebooks (Chua and the pinched loop; linear
ion drift and windows; VTEAM; Stanford–PKU and Yakopcic; pulses and neuromorphic use;
benchmarking, numerics, fitting and the library). They are generated from `build/*.py`
(`python build/assemble.py`, `python build/execute.py`); never edit an `.ipynb`.

## Command-line runs and audit logs

`python scripts/memristec_tools.py --model yakopcic2013 --stimulus sin
--amplitude 1 --frequency 1 --cycles 2 --outdir out` writes
`out/<model>_<stimulus>_A<amp>V_F<freq>Hz.csv` (`t,v,i,x`) and a JSON audit
record under `out/logs/`; `--selftest` runs the built-in physics checks.
