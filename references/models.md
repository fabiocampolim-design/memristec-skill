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
| Stanford_PKU | doi:10.1109/TED.2016.2545412 (Jiang et al., Stanford–PKU RRAM model, *IEEE TED* 63(5) 2016) | clean-room (fitting target) |
| TUD_Schroedter_2022 | doi:10.1109/MOCAST54814.2022.9837726 | adapter-only first (implicit current equation), clean-room after reading the paper |
| Threshold_Switching_KumarWilliams2017 | doi:10.1038/s41467-017-00773-4 (Kumar & Williams, *Nat. Commun.* 8, 658, 2017) | clean-room (thermal threshold switch) |
| Threshold_Switching_KumarWilliams_Simplified2020 | doi:10.1109/ISCAS45731.2020.9181036 | clean-room |
| Threshold_Switching_Pershin2013 | no DOI in the json; paper to identify | adapter-only |
| Threshold_Switching_PickettWilliams2012 | doi:10.1088/0957-4484/23/21/215202 (Pickett & Williams, *Nanotechnology* 23, 215202, 2012) | json-only upstream; clean-room from the paper |
| Threshold_Switching_PickettWilliams_Simplified2022 | doi:10.35848/1347-4065/ac8489 | clean-room |
| VTEAM2015 | doi:10.1109/TCSII.2015.2433536 (Kvatinsky et al., *IEEE TCAS-II* 62(8), 786, 2015) | clean-room |

The per-model decision is recorded here when it is taken; a model with no
paper stays adapter-only.
