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
