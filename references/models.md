# Models — equations, citations, parameters, IP status

Every model in `scripts/memristec_tools.py` is written from the paper cited
here. No line of the MemrisTec Model Library is in this product; the optional
cross-check (`scripts/upstream_adapter.py`) runs *your* local clone and
compares numbers. The state variable is always `x ∈ [0, 1]`; the driver
clips it there after each step.

## `linear_ion_drift` — Strukov 2008 with a window

**Equations.** `x = w/D` is the doped fraction of the oxide thickness `D`.

```
R(x)  = R_on x + R_off (1 - x)
i     = v / R(x)
dx/dt = k i f(x, i),      k = mu_v R_on / D^2
```

Windows `f(x, i)` (`window=` argument):

| name | f(x, i) | reference |
|---|---|---|
| `none` | 1 | Strukov et al. 2008, eq. 5–6 |
| `joglekar` | 1 − (2x − 1)^(2p) | Joglekar & Wolf 2009, eq. 12 |
| `biolek` | 1 − (x − stp(−i))^(2p), stp(u) = 1 for u ≥ 0 else 0 | Biolek, Biolek & Biolková 2009, eq. 8 |
| `prodromakis` | j · (1 − [(x − 0.5)² + 0.75]^p) | Prodromakis et al. 2011, eq. 3 |

Without a window the memristance is affine in charge, `M(q) = R_off −
(R_off − R_on) k q` — that is Strukov's eq. 6 and the physics check in
`tests/test_linear_ion_drift.py` and `scripts/verify_memristec.py`. The
Joglekar window vanishes at both ends (terminal-state problem: once `x`
reaches 0 or 1 it cannot leave). The Biolek window vanishes only at the end
the current is pushing towards, so a reversed current frees the state. The
Prodromakis window is bounded by `j` and never negative on `[0, 1]`.

**Citations.**

- D. B. Strukov, G. S. Snider, D. R. Stewart, R. S. Williams, "The missing
  memristor found", *Nature* 453, 80–83 (2008). doi:10.1038/nature06932
- Y. N. Joglekar, S. J. Wolf, "The elusive memristor: properties of basic
  electrical circuits", *Eur. J. Phys.* 30, 661–675 (2009).
  doi:10.1088/0143-0807/30/4/001
- Z. Biolek, D. Biolek, V. Biolková, "SPICE model of memristor with
  nonlinear dopant drift", *Radioengineering* 18(2), 210–214 (2009).
- T. Prodromakis, B. P. Peh, C. Papavassiliou, C. Toumazou, "A versatile
  memristor model with nonlinear dopant kinetics", *IEEE Trans. Electron
  Devices* 58(9), 3099–3105 (2011). doi:10.1109/TED.2011.2158004

**Default parameters** (`LinearIonDrift.defaults`).

| parameter | default | origin |
|---|---|---|
| `R_on` | 100 Ω | Strukov 2008 Fig. 2 device (R_off/R_on = 160) |
| `R_off` | 16 kΩ | same |
| `D` | 10 nm | Strukov 2008 (TiO₂ film thickness) |
| `mu_v` | 1e-14 m² s⁻¹ V⁻¹ | Strukov 2008 (dopant mobility) |
| `p` | 10 | Joglekar & Wolf 2009 (typical exponent) |
| `j` | 1.0 | Prodromakis 2011 (scaling factor) |
| `x0` | 0.1 | ours: an initial state away from both boundaries |

Any parameter can be overridden: `LinearIonDrift(window="biolek",
R_off=38e3, x0=0.26)` reproduces the numbers the upstream `HP_Biolek2009`
folder reads from its `model.yml` (R_init = 28 kΩ → x0 = (38k − 28k)/(38k −
100) ≈ 0.264).

**IP status.** Written from the papers; no upstream code.

**Cross-check.** `tests/test_upstream_crosscheck.py` compares the `joglekar`
variant with the upstream folder **`HP_Biolek2009`** — because that folder,
despite its name, implements the Joglekar window (finding **P-1**,
`docs/03-model-library-audit.md` §4 of the study repo). Measured 2026-09-02
on clone `f13423f`: max relative difference of dx/dt 3.7e-16, of i 0; our
`biolek` variant differs from the same folder by more than 0.1 near the
boundaries. Tolerances: `tests/records/crosscheck_v1.json`.

## `yakopcic2013` — Yakopcic 2011/2013

**Equations.**

```
i(t)   = a1 x sinh(b v)   for v >= 0
       = a2 x sinh(b v)   for v <  0
dx/dt  = eta g(v) f(x, v)
g(v)   =  Ap (e^v  - e^Vp)   for v >  Vp
       = -An (e^-v - e^Vn)   for v < -Vn
       =  0                  otherwise
f(x,v) = e^{-alphap (x - xp)} wp(x)     for eta v >= 0 and x >= xp;   1 for x < xp
       = e^{ alphan (x + xn - 1)} wn(x)  for eta v <  0 and x <= 1 - xn; 1 otherwise
wp(x)  = (xp - x)/(1 - xp) + 1
wn(x)  = x / (1 - xn)
```

`g` is the voltage threshold (no state motion for −Vn ≤ v ≤ Vp), `f` the
boundary-decay function (motion slows exponentially beyond `xp` / `1 − xn`
and stops at the boundary because `wp(1) = 0`, `wn(0) = 0`). `eta = ±1`
sets the direction of motion relative to the voltage.

**Citations.**

- C. Yakopcic, T. M. Taha, G. Subramanyam, R. E. Pino, S. Rogers, "A
  memristor device model", *IEEE Electron Device Lett.* 32(10), 1436–1438
  (2011). doi:10.1109/LED.2011.2163292
- C. Yakopcic, T. M. Taha, G. Subramanyam, R. E. Pino, "Generalized
  memristive device SPICE model and its application in circuit design",
  *IEEE Trans. Comput.-Aided Des. Integr. Circuits Syst.* 32(8), 1201–1214
  (2013). doi:10.1109/TCAD.2013.2252057

**Default parameters** (`Yakopcic2013.defaults`): `a1 = a2 = 0.17`, `b =
0.05`, `Vp = 0.16`, `Vn = 0.15`, `Ap = An = 4000`, `xp = 0.3`, `xn = 0.5`,
`alphap = 1`, `alphan = 5`, `eta = 1`, `x0 = 0.11`. This is the parameter
set of the 2013 paper's example device, and the set the upstream
`Yakopcic2013` folder hard-codes; the cross-check reads the upstream values
at run time and instantiates our model with them, so equality of the two
derivative fields is measured, not assumed. Checking the numbers line by
line against Table I of the paper is a follow-up item (the paper is not in
the study repo yet).

**IP status.** Written from the papers; no upstream code.

**Cross-check.** `tests/test_upstream_crosscheck.py` vs upstream
`Yakopcic2013`: derivative and current relative difference 0 on a 25×21
`(x, v)` grid, trajectory difference 0 under a 1 V, 1 Hz sine (2026-09-02,
clone `f13423f`). Note the upstream `simulate()` ignores its `V` argument
(finding **P-2**); the cross-check therefore drives *both* derivative
fields with our `simulate`.

## `vteam2015` — VTEAM, Kvatinsky et al. 2015

**Equations** (paper eq. 1–3; normalised state `x = (w − w_on)/(w_off − w_on)`, so
`x = 0` is `R_on` and `x = 1` is `R_off` — note the opposite convention to
`linear_ion_drift`):

```
dx/dt = k_off (v/v_off − 1)^alpha_off f(x)     v > v_off > 0      (RESET direction)
      = k_on  (v/v_on  − 1)^alpha_on  f(x)     v < v_on  < 0      (SET direction)
      = 0                                      v_on ≤ v ≤ v_off  (dead band)
i     = v / [R_on + (R_off − R_on) x]
```

`f(x)` is the rectangular window (`window=1`: 1 inside (0, 1), 0 at the ends,
with a rate pointing inward always allowed so the state can leave a boundary;
`window=0`: f = 1 and the driver's clip bounds the state). `k_on < 0`, `k_off > 0`
are rates of the normalised state in 1/s (the paper's m/s divided by
`w_off − w_on`). The paper's exponential resistance dependence (its eq. 4) is not
implemented.

**Citation.** S. Kvatinsky, M. Ramadan, E. G. Friedman, A. Kolodny, "VTEAM: a
general model for voltage-controlled memristors", *IEEE Trans. Circuits Syst.
II* 62(8), 786–790 (2015). doi:10.1109/TCSII.2015.2433536

**Default parameters** (`VTEAM2015.defaults`) — all **ours, illustrative** (a
device that switches fully in ~0.1 s at twice its threshold): `R_on = 1 kΩ`,
`R_off = 100 kΩ`, `v_on = −0.3 V`, `v_off = 0.3 V`, `k_on = −10 s⁻¹`,
`k_off = 10 s⁻¹`, `alpha_on = alpha_off = 3`, `window = 1`, `x0 = 0.5`. The
paper's fitted sets (its Table I) are to be checked against the paper, which is
not in the study repo yet.

**IP status.** Written from the paper; no upstream code.

**Cross-check.** `tests/test_upstream_crosscheck.py` vs upstream `VTEAM2015`:
the shim converts their `w` (metres, in `[w_on, w_off]`) and rates (m/s) to our
normalised state. Measured 2026-09-03 on clone `f13423f`: max relative
difference of dx/dt 2.0e-16 and of i 2.1e-16 on a 25×16 `(x, v)` grid outside
the dead band, both fields exactly zero inside it, trajectory difference
5e-18 under a 0.3 V, 100 Hz sine. The parameter set read from their
`model.yml` (`R_on = 387 Ω`, `R_off = 1069.5 Ω`, `v_on = −0.15 V`,
`v_off = 0.16 V`, normalised `k_on = −2.2e4 s⁻¹`, `k_off = 249 s⁻¹`,
`α = 3`, `x0 = 0.89`) is a fitted device set, not our defaults; both run
through the same equations. Tolerances: `tests/records/crosscheck_v1.json`.

## `stanford_pku2016` — Stanford–PKU RRAM model, Jiang et al. 2016

**Equations** (paper eq. 1–4). State: tunnelling gap `g ∈ [g_min, g_max]`,
normalised `x = (g_max − g)/(g_max − g_min)` so that `x = 1` is the smallest gap
(low-resistance state), as for `linear_ion_drift`.

```
i     = I0 exp(−g/g0) sinh(v/V0)
dg/dt = −nu0 exp(−Ea q / kT) sinh( gamma (a0/t_ox) q v / kT )
gamma = gamma0 − beta (g / 1 nm)^alpha            (alpha = 3 in the paper)
T     = T0 + |v i| R_th
dx/dt = −(dg/dt) / (g_max − g_min)
```

A positive voltage closes the gap (SET); the Joule term `|v i| R_th` raises the
local temperature and accelerates the ion motion, which is why SET is abrupt
and rate-dependent (V_set ≈ 0.47 V at 1 Hz, 1.08 V at 1 kHz, 1.45 V at 100 kHz
with the defaults, 20 000 points per period). Both sinh arguments are limited to
`±clip_arg` — a numerical guard, not part of the paper.

**Citation.** Z. Jiang, Y. Wu, S. Yu, L. Yang, K. Song, Z. Karim, H.-S. P. Wong,
"A compact model for metal–oxide resistive random access memory with
experiment verification", *IEEE Trans. Electron Devices* 63(5), 1884–1892
(2016). doi:10.1109/TED.2016.2545412

**Default parameters** (`StanfordPKU2016.defaults`).

| parameter | default | origin |
|---|---|---|
| `g0` | 0.25 nm | paper (HfOx set), as recalled — to check against Table I |
| `V0` | 0.25 V | same |
| `nu0` | 10 m/s | same |
| `Ea` | 0.6 eV | same |
| `a0` | 0.25 nm | same |
| `t_ox` | 12 nm | same |
| `gamma0`, `beta`, `alpha` | 16, 0.8, 3 | same |
| `T0` | 298 K | same |
| `R_th` | 2.1e3 K/W | same |
| `I0` | 1e-4 A | ours (teaching loop; the paper's value is larger) |
| `g_min`, `g_max` | 0.4 nm, 1.7 nm | ours (HRS/LRS ≈ 180 at 0.1 V) |
| `clip_arg` | 40 | ours (numerical guard) |
| `x0` | 0 | ours: start in HRS |

**IP status.** Written from the paper; no upstream code.

**Numerics.** The gap dynamics are stiff near SET: use `n_per_cycle ≥ 20000`
with `rk4` (`references/pitfalls.md`); `method="ivp"` with the driver's
`max_step` is ~10× slower and can miss the RESET branch.

**Cross-check.** `tests/test_upstream_crosscheck.py` vs upstream `Stanford_PKU`:
the shim maps their gap (metres) and their `gamma = gamma0 − beta g^alpha` with
`g` in metres to our nm-normalised form (`beta_ours = beta (1e-9)^alpha`).
Measured 2026-09-03 on clone `f13423f`: max relative difference of dx/dt
3.5e-15 and of i 0 on a 25×21 `(x, v)` grid over ±1.5 V. Their parameter set
(hard-coded in `__init__`: `Ea = 1.24 eV`, `nu0 = 200 m/s`, `gamma0 = 4.8`,
`alpha = 1.1`, `t_ox = 7.1 nm`, `R_th = 500 K/W`, gap 0.20–1.15 nm) differs from
ours and from the paper's HfOx set; the equations agree. Their folder's own
`run_loop()` cannot run (finding **P-6**: it instantiates an undefined
`MemristorModel`). Tolerances: `tests/records/crosscheck_v1.json`.

## The other upstream folders (planned)

Status vocabulary: **clean-room** = we will write it from the paper;
**adapter-only** = runnable through `upstream_adapter.py` from your own
clone, never shipped (no paper with the full equation set, or too large to
re-derive now); **json-only** = upstream has metadata but no code.

| upstream folder (`main`) | paper (DOI from upstream `model.json` unless noted) | planned status |
|---|---|---|
| HP_Joglekar2009 | Joglekar & Wolf 2009 (above) | json-only upstream; **covered** by `linear_ion_drift` window `joglekar` |
| HP_Prodromakis2011 | Prodromakis et al. 2011 (above) | **covered** by window `prodromakis`; adapter shim to add |
| DataDriven2021 | json gives a dataset DOI (10.5258/SOTON/D0132), no paper; the Southampton data-driven ReRAM model line (Messaris et al., IEEE TCAD 2018, doi:10.1109/TCAD.2018.2791468) is the likely source — to verify | adapter-only until the paper is confirmed |
| JART_VCM_v1_simplified, JART_VCM_varV1_Simplified | doi:10.1088/2634-4386/ad57e7 (JART VCM simplified, *Neuromorph. Comput. Eng.* 2024) | clean-room (fitting target for the owner's TaOx device) |
| MEMMEA2025 | doi:10.1002/aelm.202400765 | json-only upstream; clean-room only if the paper states the full equation set |
| Stanford_PKU | Jiang et al. 2016 (below) | **clean-room** — `stanford_pku2016` (fitting target) |
| TUD_Schroedter_2022 | doi:10.1109/MOCAST54814.2022.9837726 | adapter-only first (implicit current equation), clean-room after reading the paper |
| Threshold_Switching_KumarWilliams2017 | doi:10.1038/s41467-017-00773-4 (Kumar & Williams, *Nat. Commun.* 8, 658, 2017) | clean-room (thermal threshold switch) |
| Threshold_Switching_KumarWilliams_Simplified2020 | doi:10.1109/ISCAS45731.2020.9181036 | clean-room |
| Threshold_Switching_Pershin2013 | no DOI in the json; paper to identify | adapter-only |
| Threshold_Switching_PickettWilliams2012 | doi:10.1088/0957-4484/23/21/215202 (Pickett & Williams, *Nanotechnology* 23, 215202, 2012) | json-only upstream; clean-room from the paper |
| Threshold_Switching_PickettWilliams_Simplified2022 | doi:10.35848/1347-4065/ac8489 | clean-room |
| VTEAM2015 | Kvatinsky et al. 2015 (below) | **clean-room** — `vteam2015` |

The per-model decision is recorded here when it is taken; a model with no
paper stays adapter-only.
