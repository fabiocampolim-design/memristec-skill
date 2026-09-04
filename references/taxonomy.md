# Memristor types, model families and data — one map

Where a device, a model and a data set sit relative to each other. The vocabulary of the
first table is the one the MemrisTec model table uses in each folder's `model.json`
(`references/platform.md`: `physics`, `switchingType`, `switchingGeometry`, `volatility`);
the model column names this toolkit's clean-room models and the library folders.

## 1. Device classes (by switching mechanism)

| class (`physics`) | what moves | `switchingType` | `switchingGeometry` | `volatility` | typical stack | models that describe it |
|---|---|---|---|---|---|---|
| **Valence change memory (VCM)** | oxygen vacancies form / dissolve a conductive filament (or modulate an interface) in a transition-metal oxide | bipolar | filamentary (also area-dependent in interface-type cells) | non-volatile | Pt/TaOx/Ta, TiN/HfOx/Ti, W/TaOx/W | `stanford_pku2016` (gap-based, self-heating); upstream `JART_VCM_*` (Schottky + plug/disc, planned); phenomenologically `vteam2015`, `yakopcic2013`; the linear-ion-drift family as the historical TiO₂ picture |
| **Electrochemical metallization (ECM, CBRAM)** | metal cations (Ag, Cu) from an active electrode form a metallic filament | bipolar | filamentary | non-volatile (thin filaments can be volatile: diffusive memristors) | Ag/SiO₂/Pt, Cu/GeS/W | no library folder yet; `vteam2015` / `yakopcic2013` as phenomenological fits |
| **Thermochemical memory (TCM)** | Joule heating drives a redox reaction; the filament ruptures thermally | unipolar | filamentary | non-volatile | Pt/NiO/Pt | none shipped; a thermal model (temperature state) is required |
| **Phase change memory (PCM)** | crystalline ↔ amorphous phase of a chalcogenide, set by melt-quench | unipolar (current-driven) | volume | non-volatile, drifts | Ge₂Sb₂Te₅ | outside this toolkit's single-state ODE (needs a thermal + crystallisation state) |
| **Threshold switches (Mott / thermal, e.g. NbO₂, VO₂)** | temperature-driven insulator–metal transition; the state is the temperature | current-controlled NDR | filamentary | **volatile** (relaxes when the current stops) | Pt/NbO₂/Pt | upstream `Threshold_Switching_KumarWilliams*`, `…PickettWilliams*` (adapter-only for now); `Threshold_Switching_Pershin2013` (voltage thresholds, non-thermal) |
| **Interface / area-dependent** | uniform modulation of a Schottky or tunnel barrier over the whole area (a VCM sub-type) | bipolar | area-dependent | non-volatile, analogue | Pr₀.₇Ca₀.₃MnO₃, TaOx interface cells | no dedicated folder; the linear-ion-drift family (state = doped fraction of a uniform film) is closest in spirit |
| **Data-driven** | not a mechanism: an interpolation of measured transitions | as measured | as measured | as measured | Southampton dataset (`doi:10.5258/SOTON/D0132`) | upstream `DataDriven2021` (adapter-only) |

Ferroelectric and magnetic tunnel junctions are memristive by Chua's definition but are not
in the library and not in this toolkit.

## 2. Model families (by what the state variable is)

| family | state variable | physics content | toolkit / library | good for | not for |
|---|---|---|---|---|---|
| Linear ion drift + window | doped fraction `w/D` of a uniform film | Strukov's charge-controlled memristance; windows are numerical boundary fixes | `linear_ion_drift` (none / joglekar / biolek / prodromakis); upstream `HP_*` | teaching Chua's definition, the pinched loop, frequency dependence, terminal-state problem | any real device: no threshold, moves under every read |
| Generalised phenomenological (Yakopcic) | abstract `x`, current `∝ x sinh(bv)` | voltage threshold `g(v)`, exponential boundary decay `f(x)`, direction switch `η` | `yakopcic2013`; upstream `Yakopcic2013` | fitting many published devices with one equation set; neuromorphic simulation | extracting physical parameters |
| Threshold phenomenological (TEAM / VTEAM) | normalised filament length `x`, `x = 0` is `R_on` | dead band `[v_on, v_off]`, power-law overdrive, rectangular window | `vteam2015`; upstream `VTEAM2015` | circuit-level memory and crossbar design, pulse programming tables | thermal effects, variability |
| Physics-based filamentary VCM (Stanford–PKU, JART) | tunnelling gap `g` (Stanford–PKU); disc oxygen-vacancy concentration + temperature (JART) | field-driven ion hopping, Joule self-heating, Schottky/tunnel conduction | `stanford_pku2016`; upstream `Stanford_PKU`, `JART_VCM_*` (planned clean-room) | fitting HfOx / TaOx devices, sweep-rate dependence, forming-free bipolar cells (the owner's device) | ECM, unipolar, volatile devices |
| Thermal threshold (Kumar–Williams, Pickett–Williams) | filament temperature `T` (+ sometimes a second state) | heat balance `C_th dT/dt = iv − (T − T_amb)/R_th` with a temperature-dependent conductance | upstream only (adapter) | NbO₂ oscillators, selectors, chaotic dynamics | non-volatile memory |
| Data-driven | measured lookup tables | none | upstream `DataDriven2021` (adapter) | reproducing one measured device family | extrapolation |

## 3. Data sets and how they map onto the two tables

| data | what it is | device class (§1) | model family to fit (§2) | where |
|---|---|---|---|---|
| Owner's W/TaOx/W and W/Zr:TaOx/W cells (Palhares et al. 2021, *Nanotechnology* 32, 405202) | DC sweeps (V_SET ≈ V_RESET ≈ 2–2.3 V, LRS 0.7–3.7 kΩ, HRS 15–47 kΩ at 0.2 V), 200-pulse LTP/LTD (600 ns / 200 µs), device-to-device statistics, hopping-transport J–E fits | VCM, bipolar, filamentary, forming-free, non-volatile | Stanford–PKU (gap + self-heating) and JART VCM for the sweeps; pulse tables (`pulse_response`) for LTP/LTD; Yakopcic as the phenomenological fallback | `data-private/` (gitignored) when the measurement files arrive; fitting workflow = follow-up plan |
| Southampton ReRAM dataset (`doi:10.5258/SOTON/D0132`) | measured switching transitions used to build `DataDriven2021` | as measured (TiO₂-class VCM in the Southampton line — to verify) | none: the data *is* the model | upstream only |
| The library's own `imageIV` / `imageDynamic` plots | one quasi-static loop and one dynamic route map per folder, generated by the folder's runner | per folder (`model.json`) | the folder's own model | upstream only; our chapters regenerate the equivalents |
| Synthetic data of chapter 6 §23 | VTEAM loops with known parameters (+ 1 % noise in exercise 6.1) | — | VTEAM (identifiability lesson: a saturating drive carries no information about the rate) | `chapters/Memristec_06_*` |

## 4. How to choose (the questions to ask a device before picking a model)

1. **Volatile or not?** Volatile → a thermal threshold model (adapter-only today). Non-volatile → continue.
2. **Bipolar or unipolar?** Unipolar (TCM, PCM) → not covered by the shipped single-state models. Bipolar → continue.
3. **Filamentary or area-dependent?** Filamentary VCM/ECM → Stanford–PKU (physics) or VTEAM / Yakopcic (phenomenological). Area-dependent / analogue → linear-ion-drift-like state, Yakopcic for fitting.
4. **What must the model reproduce?** Only loops and thresholds → VTEAM. Sweep-rate dependence and self-heating → Stanford–PKU. Many devices with one equation set → Yakopcic. Pulse LTP/LTD tables for a framework → any of them through `pulse_response` (chapter 5).
5. **What data exist?** DC sweeps only → the loop-fitting recipe (chapter 6 §23, mind identifiability). Pulse trains → fit `pulse_response` curves. Statistics over devices → JART-class variability models (planned).

The `model.json` fields of the library encode exactly the answers to questions 1–3 for
each folder (`references/platform.md`); the folder-by-folder audit is in the study
repository (`docs/03-model-library-audit.md`).
