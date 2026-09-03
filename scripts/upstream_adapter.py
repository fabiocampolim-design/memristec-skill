# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""upstream_adapter — run models of a *local* MemrisTec Model Library clone and
compare them with memristec_tools' clean-room models (S4 confidence check).

The library has no common interface: each models/<Name>/model.py defines its
own class and method names. SHIMS maps a folder name to a small wrapper that
exposes state_derivative(x, v) / current(x, v) / x0 / params. Nothing from the
library is copied here; it is imported by file path at run time.

Usage:
    MEMRISTEC_MODEL_LIBRARY=<clone> python scripts/upstream_adapter.py --model Yakopcic2013 [--outdir DIR] [--log-dir DIR] [-q]
    python scripts/upstream_adapter.py --library <clone> --model HP_Biolek2009
    python scripts/upstream_adapter.py --version
Exit code 0 on success, 1 when a comparison exceeds tests/records tolerances, 2 on usage error, 3 when no library is available.
"""

import argparse
import datetime
import importlib.util
import json
import os
import platform
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from memristec_tools import LinearIonDrift, StanfordPKU2016, VTEAM2015, Yakopcic2013, __version__, simulate  # noqa: E402


def find_library():
    p = os.environ.get("MEMRISTEC_MODEL_LIBRARY")
    return p if p and os.path.isdir(os.path.join(p, "models")) else None


def _import_model_file(path):
    spec = importlib.util.spec_from_file_location("upstream_" + os.path.basename(os.path.dirname(path)), path)
    mod = importlib.util.module_from_spec(spec)
    cwd = os.getcwd()
    os.chdir(os.path.dirname(path))      # their loaders resolve model.yml relative to the file
    try:
        spec.loader.exec_module(mod)
    finally:
        os.chdir(cwd)
    return mod


class UpstreamModel:
    def __init__(self, name, source, obj, dxdt, current, x0, params):
        self.name, self.source, self.obj = name, source, obj
        self._dxdt, self._current, self.x0, self.params = dxdt, current, float(x0), params

    def state_derivative(self, x, v):
        return float(self._dxdt(x, v))

    def current(self, x, v):
        return float(self._current(x, v))

    @staticmethod
    def clip(x):
        """Same state interval as memristec_tools.Model so simulate() can drive it."""
        return min(1.0, max(0.0, float(x)))


def _shim_hp_biolek2009(mod, source):
    obj = mod.HP_Biolek2009()
    params = {"R_on": float(obj.Ron), "R_off": float(obj.Roff), "D": float(obj.D),
              "mu_v": float(obj.uv), "p": int(obj.p), "x0": float(obj.x0)}
    return UpstreamModel("HP_Biolek2009", source, obj,
                         dxdt=lambda x, v: obj.dxdt(0.0, x, v),
                         current=lambda x, v: obj.memristor_current(v, x),
                         x0=obj.x0, params=params)


def _shim_yakopcic2013(mod, source):
    obj = mod.Memristor()
    keys = ("a1", "a2", "b", "Vp", "Vn", "Ap", "An", "xp", "xn", "alphap", "alphan", "eta")
    params = {k: float(getattr(obj, k)) if k != "eta" else int(getattr(obj, k)) for k in keys}
    params["x0"] = float(obj.xo)
    return UpstreamModel("Yakopcic2013", source, obj,
                         dxdt=lambda x, v: obj.dxdt(0.0, x, v),
                         current=lambda x, v: obj.IVRel(v, x),
                         x0=obj.xo, params=params)


def _shim_vteam2015(mod, source):
    obj = mod.VTEAM2015()
    span = float(obj.w_off) - float(obj.w_on)              # metres; our x = (w - w_on) / span
    params = {"R_on": float(obj.Ron), "R_off": float(obj.Roff),
              "v_on": float(obj.v_on), "v_off": float(obj.v_off),
              "k_on": float(obj.kon) / span, "k_off": float(obj.koff) / span,
              "alpha_on": float(obj.alpha_on), "alpha_off": float(obj.alpha_off),
              "window": 1, "x0": (float(obj.w0) - float(obj.w_on)) / span}

    def w_of(x):
        return float(obj.w_on) + x * span

    return UpstreamModel("VTEAM2015", source, obj,
                         dxdt=lambda x, v: obj.dw_dt(0.0, w_of(x), v) / span,
                         current=lambda x, v: obj.current(v, w_of(x)),
                         x0=params["x0"], params=params)


def _shim_stanford_pku(mod, source):
    obj = mod.Stanford_PKU()
    span = float(obj.g_max_m) - float(obj.g_min_m)          # metres; our x = (g_max - g) / span
    alpha = float(obj.alpha)
    params = {"I0": float(obj.I0_A), "g0": float(obj.g0_m), "V0": float(obj.V0_V),
              "nu0": float(obj.nu0_mps), "Ea": float(obj.Ea_eV), "a0": float(obj.a0_m),
              "t_ox": float(obj.tOX_m), "gamma0": float(obj.gamma0),
              "beta": float(obj.beta) * (1e-9) ** alpha,     # their gamma uses g in metres
              "alpha": alpha, "T0": float(obj.T0_K), "R_th": float(obj.RTH_KW),
              "g_min": float(obj.g_min_m), "g_max": float(obj.g_max_m),
              "clip_arg": 40.0, "x0": (float(obj.g_max_m) - float(obj.g)) / span}

    def g_of(x):
        return float(obj.g_max_m) - x * span

    def dxdt(x, v):
        g = g_of(x)
        i = obj.I(g, v)
        # their T_of(V, I) = T0 + V I R_th has no abs(); V I >= 0 for this current law, so it equals our |v i| form
        return -obj.dgdt(g, v, obj.T_of(v, i)) / span

    return UpstreamModel("Stanford_PKU", source, obj, dxdt=dxdt,
                         current=lambda x, v: obj.I(g_of(x), v),
                         x0=params["x0"], params=params)


SHIMS = {"HP_Biolek2009": _shim_hp_biolek2009, "Yakopcic2013": _shim_yakopcic2013,
         "VTEAM2015": _shim_vteam2015, "Stanford_PKU": _shim_stanford_pku}
OURS = {"HP_Biolek2009": lambda p: LinearIonDrift(window="joglekar", **p),
        "Yakopcic2013": lambda p: Yakopcic2013(**p),
        "VTEAM2015": lambda p: VTEAM2015(**p),
        "Stanford_PKU": lambda p: StanfordPKU2016(**p)}


def load_upstream(name, library):
    if name not in SHIMS:
        raise ValueError(f"no shim for {name!r}; available: {sorted(SHIMS)}")
    source = os.path.join(library, "models", name, "model.py")
    if not os.path.isfile(source):
        raise FileNotFoundError(source)
    return SHIMS[name](_import_model_file(source), source)


def _rel(a, b):
    den = max(abs(a), abs(b), 1e-300)
    return abs(a - b) / den


def crosscheck(ours, theirs, x_grid, v_grid):
    """Max absolute / relative differences of dx/dt and i over the (x, v) grid."""
    abs_d = abs_i = rel_d = rel_i = 0.0
    n = 0
    for x in x_grid:
        for v in v_grid:
            d0, d1 = ours.state_derivative(float(x), float(v)), theirs.state_derivative(float(x), float(v))
            i0, i1 = ours.current(float(x), float(v)), theirs.current(float(x), float(v))
            abs_d, abs_i = max(abs_d, abs(d0 - d1)), max(abs_i, abs(i0 - i1))
            if d0 != 0.0 or d1 != 0.0:
                rel_d = max(rel_d, _rel(d0, d1))
            if i0 != 0.0 or i1 != 0.0:
                rel_i = max(rel_i, _rel(i0, i1))
            n += 1
    return {"max_abs_dxdt": abs_d, "max_rel_dxdt": rel_d, "max_abs_i": abs_i, "max_rel_i": rel_i, "n": n}


def trajectory_crosscheck(ours, theirs, amplitude, frequency, cycles=1, n_per_cycle=2000):
    """Integrate both derivative fields with the same rk4 on the same sine; compare x and i."""
    t = np.linspace(0.0, cycles / frequency, int(cycles * n_per_cycle) + 1)
    v = amplitude * np.sin(2 * np.pi * frequency * t)
    a, b = simulate(ours, t, v, "rk4"), simulate(theirs, t, v, "rk4")
    return {"max_abs_x": float(np.max(np.abs(a.x - b.x))), "max_abs_i": float(np.max(np.abs(a.i - b.i)))}


def build_parser():
    ap = argparse.ArgumentParser(prog="upstream_adapter", description=__doc__.splitlines()[0])
    ap.add_argument("--library", default=None, help="path to a local clone (default: $MEMRISTEC_MODEL_LIBRARY)")
    ap.add_argument("--model", choices=sorted(SHIMS), help="upstream folder to compare (default: all shims)")
    ap.add_argument("--outdir", default="./out", help="output directory (default ./out)")
    ap.add_argument("--log-dir", default=None, help="audit-log directory (default <outdir>/logs)")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the verdict")
    ap.add_argument("--version", action="version", version=f"memristec-skill {__version__}")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    lib = args.library or find_library()
    if not lib:
        print("no library: set MEMRISTEC_MODEL_LIBRARY or pass --library")
        return 3
    with open(os.path.join(ROOT, "tests", "records", "crosscheck_v1.json"), encoding="utf-8") as f:
        tol = json.load(f)["models"]
    names = [args.model] if args.model else sorted(SHIMS)
    results, ok = {}, True
    for name in names:
        theirs = load_upstream(name, lib)
        ours = OURS[name](theirs.params)
        r = crosscheck(ours, theirs, np.linspace(0.01, 0.99, 25), np.linspace(-1.2, 1.2, 25))
        r.update(trajectory_crosscheck(ours, theirs, 1.0, 1.0))
        r["within_tolerance"] = r["max_rel_dxdt"] <= tol[name]["max_rel_dxdt"] and r["max_rel_i"] <= tol[name]["max_rel_i"]
        ok &= r["within_tolerance"]
        results[name] = r
        if not args.quiet:
            print(f"[{'PASS' if r['within_tolerance'] else 'FAIL'}] {name}: rel dxdt {r['max_rel_dxdt']:.2e}, rel i {r['max_rel_i']:.2e}, traj x {r['max_abs_x']:.2e}")
    log_dir = args.log_dir or os.path.join(args.outdir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(log_dir, f"upstream_adapter_{stamp}_{os.getpid()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tool": "upstream_adapter", "version": __version__, "argv": argv, "utc": stamp,
                   "python": platform.python_version(), "platform": platform.platform(),
                   "library": lib, "ok": ok, "results": results}, f, indent=2)
    print(("crosscheck OK" if ok else "crosscheck FAILED") + f" (log {path})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
