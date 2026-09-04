# Pitfalls — numerical traps met while building this toolkit

1. **High-order windows freeze the state.** With `p = 10` the Joglekar and
   Biolek windows are ≈ 1 only in the middle of `[0, 1]` and drop to zero
   within a few percent of either end, so `dx/dt ≈ 0` over most of the
   interval once the state gets near a boundary. Start from an `x0` away
   from 0 and 1 (the defaults do) and use at least ~1000 grid points per
   period; a coarse grid steps straight into the frozen region.

2. **Yakopcic's threshold function grows like `e^v`.** `g(v) = Ap (e^v −
   e^Vp)` with `Ap = 4000` reaches 10⁴ V⁻¹ s⁻¹ at 1 V and 10⁵ at 3 V; the
   state then switches within a few grid points. Keep `|v| ≲ 2 V` with the
   default parameters or lower `Ap`/`An`; otherwise refine the grid.

3. **`simulate(..., "ivp")` must not step over the stimulus.** SciPy's
   RK45 chooses its own step from the *state* error only; with a fast
   stimulus it can skip a half period unnoticed. The driver passes
   `max_step = Δt` of the grid; keep that if you write your own call.
   (The upstream folders call `solve_ivp` without `max_step`.)

4. **Clipping costs accuracy at a boundary hit.** The fixed-step drivers
   clip `x` to `[0, 1]` after every stage; when a trajectory actually hits
   a boundary the method degrades to first order there. The windows make
   the clip inactive in exact arithmetic, so a clip that *does* trigger
   means the grid is too coarse or the window is `none`.

5. **Integer parameters from upstream YAML.** `Ron: 100` in a `model.yml`
   is read as `int`; `int / int` and `int ** 2` are fine in Python 3, but
   NumPy integer arrays overflow silently. The adapter casts every upstream
   parameter to `float` before it reaches our models.

6. **The partial clone is not a normal clone.** With `--filter=blob:none`
   every file content is fetched on demand: `git diff branchA branchB` or
   `git log -p` pulls thousands of blobs through the Anubis proxy and
   stalls. Use `git ls-tree`, `git log` (no `-p`) and `git show
   <ref>:<path>` for the one file you need.

7. **Sign of the stimulus.** Some upstream folders drive their own sine with
   a leading minus (`VTEAM2015`) or rectify it; when comparing loops, plot
   `v` first and match the sign convention before comparing currents.

8. **Loop metrics at zero crossings.** `v / i` is undefined where `v = 0`;
   `loop_metrics` masks `|v| < 1 % max|v|` before computing `r_min`/`r_max`
   and the affine-law tests mask `|v| < 0.1 % max|v|` before dividing. Do
   the same in your own analysis.

9. **Stiff filamentary models need a fine grid.** `stanford_pku2016` closes
   its gap within a few microseconds once the Joule heating kicks in; with
   the default 2 000 points per period the SET voltage is still right to
   ~1 mV at 1 kHz, but the RESET branch and the loop area drift. Use 20 000
   points per period (`n_per_cycle=20000`) and `rk4`; do not use `ivp` for it.

10. **VTEAM's state runs the other way.** In `vteam2015` `x = 0` is `R_on`
    and a positive voltage above `v_off` *increases* x (RESET); in
    `linear_ion_drift` and `stanford_pku2016` `x = 1` is the low-resistance
    state and a positive voltage SETs. Compare conductances, not x, across
    models.

11. **Loop area is the sum of the lobes.** `loop_metrics["area"]` splits the
    trajectory at the zero crossings of v; the signed whole-trajectory value
    (`area_signed`) cancels for a symmetric pinched loop (finding N-2).

12. **Pulse edges lose most of a grid step.** The fixed-step RK4 driver
    interpolates the stimulus at the half step; across a pulse edge that
    interpolated voltage is half the pulse height, which for a threshold model
    sits inside the dead band. Each edge therefore integrates only 1/6 of a
    step (the `k1` or `k4` stage alone), so the first pulse of a train, the
    later ones and a pulse that runs into a boundary all move the state by
    slightly different amounts (~0.1 % at 400 points per period). Compare
    pulses from the second one on, exclude the clipped one, and quote
    per-pulse steps to 1 % — or align the grid so that a pulse edge falls on
    a grid point and refine it (chapter 5 §18 and exercise 5.1).
