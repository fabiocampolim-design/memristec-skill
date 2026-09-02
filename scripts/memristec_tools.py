# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""memristec_tools — compact memristor models written from their papers, one
ODE driver, I-V sweeps, pinched-loop metrics and dynamic route maps.

Models (references/models.md for the equations and citations):
  linear_ion_drift   Strukov et al. 2008 with a window: none | joglekar (2009) |
                     biolek (2009) | prodromakis (2011)
  yakopcic2013       Yakopcic et al. 2011 (EDL) / 2013 (TCAD)

Usage:
    python scripts/memristec_tools.py --selftest [--outdir DIR] [--log-dir DIR] [-q]
    python scripts/memristec_tools.py --model linear_ion_drift --stimulus sin --amplitude 1.2 --frequency 1 --cycles 2
    python scripts/memristec_tools.py --version
Exit code 0 on success, 1 on a failed check, 2 on usage error.
"""

import argparse
import datetime
import json
import math
import os
import platform
import sys
from dataclasses import dataclass

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))


def _version():
    try:
        with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


__version__ = _version()


# ------------------------------------------------------------------ stimuli

def sine(t, amplitude, frequency):
    """amplitude * sin(2 pi f t)."""
    return amplitude * np.sin(2.0 * np.pi * frequency * np.asarray(t, dtype=float))


def triangular(t, amplitude, frequency):
    """Triangle wave in [-A, A], starting at -A (MemrisTec FunctionGenerator convention)."""
    t = np.asarray(t, dtype=float)
    period = 1.0 / frequency
    return amplitude * (2.0 * np.abs(2.0 * (t / period - np.floor(t / period + 0.5))) - 1.0)


def rectangular(t, amplitude, frequency, duty=0.5):
    """+A for the first `duty` fraction of each period, -A otherwise."""
    t = np.asarray(t, dtype=float)
    period = 1.0 / frequency
    return np.where((t % period) < duty * period, amplitude, -amplitude)


STIMULI = {"sin": sine, "triangular": triangular, "rectangular": rectangular}


# ------------------------------------------------------------------ models

class Model:
    """A voltage-controlled memristive device with one state variable x in [0, 1].

    Subclasses implement state_derivative(x, v) = dx/dt and current(x, v) = i.
    `params` holds the parameter set actually used; `x0` the initial state.
    """

    name = "model"

    def __init__(self, **params):
        self.params = dict(self.defaults)
        unknown = set(params) - set(self.defaults)
        if unknown:
            raise ValueError(f"{self.name}: unknown parameter(s) {sorted(unknown)}")
        self.params.update(params)
        self.x0 = float(self.params.get("x0", 0.0))

    defaults = {"x0": 0.0}

    def state_derivative(self, x, v):
        raise NotImplementedError

    def current(self, x, v):
        raise NotImplementedError

    @staticmethod
    def clip(x):
        return min(1.0, max(0.0, float(x)))


class LinearIonDrift(Model):
    """Strukov et al. 2008, Nature 453, 80 — x = w/D is the doped fraction.

    R(x) = R_on x + R_off (1 - x);  i = v / R(x);  dx/dt = k i f(x, i),
    k = mu_v R_on / D^2.  Windows: none (f = 1), joglekar (Joglekar & Wolf
    2009, eq. 12), biolek (Biolek, Biolek & Biolková 2009, eq. 8),
    prodromakis (Prodromakis et al. 2011, eq. 3).
    """

    name = "linear_ion_drift"
    defaults = {"R_on": 100.0, "R_off": 16e3, "D": 10e-9, "mu_v": 1e-14,
                "p": 10, "j": 1.0, "x0": 0.1}
    WINDOWS = ("none", "joglekar", "biolek", "prodromakis")

    def __init__(self, window="joglekar", **params):
        if window not in self.WINDOWS:
            raise ValueError(f"unknown window {window!r}; choose from {self.WINDOWS}")
        super().__init__(**params)
        self.window = window
        p = self.params
        self.k = p["mu_v"] * p["R_on"] / p["D"] ** 2

    def resistance(self, x):
        p = self.params
        return p["R_on"] * x + p["R_off"] * (1.0 - x)

    def current(self, x, v):
        return v / self.resistance(x)

    def window_value(self, x, i):
        p = self.params["p"]
        if self.window == "none":
            return 1.0
        if self.window == "joglekar":
            return 1.0 - (2.0 * x - 1.0) ** (2 * p)
        if self.window == "biolek":
            stp = 1.0 if -i >= 0.0 else 0.0          # stp(-i): 1 when i <= 0
            return 1.0 - (x - stp) ** (2 * p)
        # prodromakis
        return self.params["j"] * (1.0 - ((x - 0.5) ** 2 + 0.75) ** p)

    def state_derivative(self, x, v):
        i = self.current(x, v)
        return self.k * i * self.window_value(x, i)


class Yakopcic2013(Model):
    """Yakopcic, Taha, Subramanyam, Pino 2013, IEEE TCAD 32, 1201 (and 2011 EDL 32, 1436).

    i(t)  = a1 x sinh(b v)  (v >= 0),  a2 x sinh(b v)  (v < 0)
    dx/dt = eta g(v) f(x, v)
    g(v)  = Ap (e^v - e^Vp)         v > Vp
          = -An (e^-v - e^Vn)       v < -Vn
          = 0                        otherwise
    f(x,v)= e^{-alphap (x - xp)} wp(x)   (eta v >= 0, x >= xp);  1 for x < xp
          = e^{ alphan (x + xn - 1)} wn(x)  (eta v < 0, x <= 1 - xn);  1 otherwise
    wp(x) = (xp - x)/(1 - xp) + 1,   wn(x) = x / (1 - xn)
    Default parameter set: the 2013 paper's example device (Table I).
    """

    name = "yakopcic2013"
    defaults = {"a1": 0.17, "a2": 0.17, "b": 0.05, "Vp": 0.16, "Vn": 0.15,
                "Ap": 4000.0, "An": 4000.0, "xp": 0.3, "xn": 0.5,
                "alphap": 1.0, "alphan": 5.0, "eta": 1, "x0": 0.11}

    def current(self, x, v):
        p = self.params
        a = p["a1"] if v >= 0 else p["a2"]
        return a * x * math.sinh(p["b"] * v)

    def g(self, v):
        p = self.params
        if v > p["Vp"]:
            return p["Ap"] * (math.exp(v) - math.exp(p["Vp"]))
        if v < -p["Vn"]:
            return -p["An"] * (math.exp(-v) - math.exp(p["Vn"]))
        return 0.0

    def f(self, x, v):
        p = self.params
        if p["eta"] * v >= 0:
            if x >= p["xp"]:
                wp = (p["xp"] - x) / (1.0 - p["xp"]) + 1.0
                return math.exp(-p["alphap"] * (x - p["xp"])) * wp
            return 1.0
        if x <= 1.0 - p["xn"]:
            wn = x / (1.0 - p["xn"])
            return math.exp(p["alphan"] * (x + p["xn"] - 1.0)) * wn
        return 1.0

    def state_derivative(self, x, v):
        return self.params["eta"] * self.g(v) * self.f(x, v)


MODELS = {"linear_ion_drift": LinearIonDrift, "yakopcic2013": Yakopcic2013}


def make_model(name, **params):
    if name not in MODELS:
        raise ValueError(f"unknown model {name!r}; choose from {sorted(MODELS)}")
    return MODELS[name](**params)


# ------------------------------------------------------------------ driver

@dataclass
class SimResult:
    t: np.ndarray
    v: np.ndarray
    i: np.ndarray
    x: np.ndarray

    def as_dict(self):
        return {"t": self.t.tolist(), "v": self.v.tolist(), "i": self.i.tolist(), "x": self.x.tolist()}


def simulate(model, t, v, method="rk4"):
    """Integrate dx/dt = model.state_derivative(x, v(t)) on the grid t.

    method: "euler" | "rk4" (fixed step on the grid; v is linearly interpolated
    at half steps) | "ivp" (scipy solve_ivp RK45 with v interpolated).
    The state is clipped to [0, 1] after every step (all models here define
    x on that interval; the windows make the clip inactive in exact
    arithmetic). Returns SimResult with i = model.current(x, v) on the grid.
    """
    t = np.asarray(t, dtype=float)
    v = np.asarray(v, dtype=float)
    if t.shape != v.shape or t.ndim != 1 or len(t) < 2:
        raise ValueError("t and v must be 1-D arrays of equal length >= 2")
    x = np.empty_like(t)
    x[0] = model.clip(model.x0)
    if method == "ivp":
        from scipy.integrate import solve_ivp

        def rhs(tt, xx):
            return [model.state_derivative(model.clip(xx[0]), float(np.interp(tt, t, v)))]

        sol = solve_ivp(rhs, (t[0], t[-1]), [x[0]], t_eval=t, method="RK45",
                        max_step=(t[1] - t[0]), rtol=1e-8, atol=1e-12)
        if not sol.success:
            raise RuntimeError(f"solve_ivp failed: {sol.message}")
        x[:] = np.clip(sol.y[0], 0.0, 1.0)
    elif method in ("euler", "rk4"):
        for n in range(len(t) - 1):
            h = t[n + 1] - t[n]
            xn, vn, vn1 = x[n], v[n], v[n + 1]
            if method == "euler":
                x[n + 1] = model.clip(xn + h * model.state_derivative(xn, vn))
            else:
                vh = 0.5 * (vn + vn1)
                k1 = model.state_derivative(xn, vn)
                k2 = model.state_derivative(model.clip(xn + 0.5 * h * k1), vh)
                k3 = model.state_derivative(model.clip(xn + 0.5 * h * k2), vh)
                k4 = model.state_derivative(model.clip(xn + h * k3), vn1)
                x[n + 1] = model.clip(xn + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0)
    else:
        raise ValueError(f"unknown method {method!r}")
    i = np.array([model.current(xx, vv) for xx, vv in zip(x, v)])
    return SimResult(t=t, v=v, i=i, x=x)


# ------------------------------------------------------------------ analysis

def iv_sweep(model, amplitude, frequency, cycles=1, n_per_cycle=2000, stimulus="sin", method="rk4"):
    """Drive `model` with `cycles` periods of the named stimulus and return the SimResult."""
    if stimulus not in STIMULI:
        raise ValueError(f"unknown stimulus {stimulus!r}; choose from {sorted(STIMULI)}")
    n = int(cycles * n_per_cycle) + 1
    t = np.linspace(0.0, cycles / frequency, n)
    v = STIMULI[stimulus](t, amplitude, frequency)
    return simulate(model, t, v, method=method)


def loop_metrics(res):
    """Pinched-hysteresis descriptors of an I-V trajectory.

    area: |closed-loop area| in the (v, i) plane by the shoelace formula over
    the whole trajectory (0 for a resistor); pinched_at_origin: |i| < 1e-3 *
    max|i| wherever |v| < 1e-3 * max|v|; r_min/r_max: min/max of v/i where
    |v| > 1e-2 * max|v|.
    """
    v, i = res.v, res.i
    area = 0.5 * abs(float(np.sum(v[:-1] * i[1:] - v[1:] * i[:-1])))
    vmax, imax = np.max(np.abs(v)), np.max(np.abs(i))
    near0 = np.abs(v) < 1e-3 * vmax
    pinched = bool(np.all(np.abs(i[near0]) <= 1e-3 * imax)) if imax > 0 else True
    mask = np.abs(v) > 1e-2 * vmax
    r = v[mask] / i[mask] if np.any(mask) and np.all(i[mask] != 0) else np.array([np.inf])
    return {"area": area, "i_max": float(i.max()), "i_min": float(i.min()),
            "pinched_at_origin": pinched, "r_min": float(r.min()), "r_max": float(r.max())}


def dynamic_route_map(model, x_grid, v_values):
    """dx/dt as a function of x for each constant voltage in v_values (Chua's DRM)."""
    x_grid = np.asarray(x_grid, dtype=float)
    return {float(v): np.array([model.state_derivative(float(x), float(v)) for x in x_grid])
            for v in v_values}


# ------------------------------------------------------------------ CLI

def selftest():
    """Quick physics checks; returns a list of {name, ok, detail}."""
    checks = []

    def add(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    res = iv_sweep(LinearIonDrift(window="biolek", R_off=38e3, x0=0.26), 1.2, 1.0, cycles=2, n_per_cycle=1000)
    met = loop_metrics(res)
    add("linear_ion_drift/biolek pinched loop", met["pinched_at_origin"] and met["area"] > 0, f"area={met['area']:.3e}")
    m = LinearIonDrift(window="joglekar")
    add("joglekar window vanishes at boundaries", abs(m.window_value(0.0, 1e-3)) < 1e-12 and abs(m.window_value(1.0, 1e-3)) < 1e-12)
    y = Yakopcic2013()
    add("yakopcic no motion below threshold", y.state_derivative(0.5, 0.1) == 0.0 and y.state_derivative(0.5, 1.0) > 0)
    res = iv_sweep(y, 1.0, 1.0, cycles=1, n_per_cycle=2000)
    add("yakopcic switches and stays bounded", res.x.max() > y.x0 and 0 <= res.x.min() and res.x.max() <= 1)
    return checks


def _audit(log_dir, argv, ok, checks, extra=None):
    os.makedirs(log_dir, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rec = {"tool": "memristec_tools", "version": __version__, "argv": list(argv),
           "utc": stamp, "python": platform.python_version(), "platform": platform.platform(),
           "ok": bool(ok), "checks": checks}
    if extra:
        rec.update(extra)
    path = os.path.join(log_dir, f"memristec_tools_{stamp}_{os.getpid()}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
    return path


def build_parser():
    ap = argparse.ArgumentParser(prog="memristec_tools", description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true", help="run the built-in physics checks and exit")
    ap.add_argument("--model", choices=sorted(MODELS), help="model to simulate")
    ap.add_argument("--window", default="joglekar", choices=LinearIonDrift.WINDOWS,
                    help="window for linear_ion_drift (default joglekar)")
    ap.add_argument("--stimulus", default="sin", choices=sorted(STIMULI), help="waveform (default sin)")
    ap.add_argument("--amplitude", type=float, default=1.0, help="peak voltage in V (default 1.0)")
    ap.add_argument("--frequency", type=float, default=1.0, help="frequency in Hz (default 1.0)")
    ap.add_argument("--cycles", type=float, default=1.0, help="number of periods (default 1)")
    ap.add_argument("--n-per-cycle", type=int, default=2000, help="grid points per period (default 2000)")
    ap.add_argument("--method", default="rk4", choices=["euler", "rk4", "ivp"], help="integrator (default rk4)")
    ap.add_argument("--outdir", default="./out", help="output directory (default ./out)")
    ap.add_argument("--log-dir", default=None, help="audit-log directory (default <outdir>/logs)")
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the verdict")
    ap.add_argument("--version", action="version", version=f"memristec-skill {__version__}")
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    log_dir = args.log_dir or os.path.join(args.outdir, "logs")
    if args.selftest:
        checks = selftest()
        ok = all(c["ok"] for c in checks)
        if not args.quiet:
            for c in checks:
                print(f"[{'PASS' if c['ok'] else 'FAIL'}] {c['name']}" + (f" — {c['detail']}" if c["detail"] else ""))
        path = _audit(log_dir, argv, ok, checks)
        print(("selftest OK" if ok else "selftest FAILED") + f" (log {path})")
        return 0 if ok else 1
    if not args.model:
        build_parser().error("--model is required unless --selftest")
    model = MODELS[args.model](window=args.window) if args.model == "linear_ion_drift" else MODELS[args.model]()
    res = iv_sweep(model, args.amplitude, args.frequency, cycles=args.cycles,
                   n_per_cycle=args.n_per_cycle, stimulus=args.stimulus, method=args.method)
    os.makedirs(args.outdir, exist_ok=True)
    name = f"{args.model}_{args.stimulus}_A{args.amplitude}V_F{args.frequency}Hz.csv"
    path = os.path.join(args.outdir, name)
    np.savetxt(path, np.column_stack([res.t, res.v, res.i, res.x]), delimiter=",", header="t,v,i,x", comments="")
    met = loop_metrics(res)
    checks = [{"name": "run", "ok": True, "detail": name}]
    _audit(log_dir, argv, True, checks, {"metrics": met, "params": model.params, "csv": path})
    if not args.quiet:
        print(json.dumps(met, indent=2))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
