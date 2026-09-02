# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Environment and physics smoke test for memristec-skill.

Checks, in order:
  1. imports and versions (numpy, scipy, matplotlib, pyyaml)
  2. linear ion drift + Biolek window: pinched loop with positive area
  3. memristance affine in charge without a window (Strukov 2008 eq. 6)
  4. Yakopcic 2013: no motion below threshold, switches under a 1 V sine
  5. upstream cross-check when MEMRISTEC_MODEL_LIBRARY (or --library) points at a clone; SKIP otherwise

Usage:
    python scripts/verify_memristec.py [-q] [--library PATH]
    python scripts/verify_memristec.py --version
Exit code 0 when every check passes, 1 otherwise.
"""

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from memristec_tools import LinearIonDrift, Yakopcic2013, __version__, iv_sweep, loop_metrics, simulate  # noqa: E402


def build_parser():
    ap = argparse.ArgumentParser(prog="verify_memristec", description=__doc__.splitlines()[0])
    ap.add_argument("-q", "--quiet", action="store_true", help="print only the final verdict")
    ap.add_argument("--library", default=None, help="local MemrisTec Model Library clone (default: $MEMRISTEC_MODEL_LIBRARY)")
    ap.add_argument("--version", action="version", version=f"memristec-skill {__version__}")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    all_ok = True

    def check(label, ok, detail=""):
        nonlocal all_ok
        all_ok &= bool(ok)
        if not args.quiet:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))

    import matplotlib
    import scipy
    import yaml
    check("imports", True, f"numpy {np.__version__}, scipy {scipy.__version__}, matplotlib {matplotlib.__version__}, pyyaml {yaml.__version__}")

    res = iv_sweep(LinearIonDrift(window="biolek", R_off=38e3, x0=0.26), 1.2, 1.0, cycles=2, n_per_cycle=1000)
    met = loop_metrics(res)
    check("linear ion drift / Biolek pinched loop", met["pinched_at_origin"] and met["area"] > 0, f"area {met['area']:.3e} V·A")

    m = LinearIonDrift(window="none", x0=0.5)
    t = np.linspace(0, 1, 20001)
    r = simulate(m, t, 0.05 * np.sin(2 * np.pi * 5 * t))
    q = np.concatenate([[0.0], np.cumsum(0.5 * (r.i[1:] + r.i[:-1]) * np.diff(t))])
    mask = np.abs(r.v) > 1e-3 * np.abs(r.v).max()
    slope = np.polyfit(q[mask], r.v[mask] / r.i[mask], 1)[0]
    expected = -(m.params["R_off"] - m.params["R_on"]) * m.k
    check("memristance affine in charge (Strukov eq. 6)", np.isclose(slope, expected, rtol=1e-3), f"slope {slope:.4e} vs {expected:.4e}")

    y = Yakopcic2013()
    ry = iv_sweep(y, 1.0, 1.0, cycles=1, n_per_cycle=2000)
    check("Yakopcic threshold and switching", y.state_derivative(0.5, 0.1) == 0.0 and ry.x.max() > y.x0 and ry.x.max() <= 1.0, f"x: {y.x0:.2f} -> {ry.x.max():.3f}")

    lib = args.library or os.environ.get("MEMRISTEC_MODEL_LIBRARY") or None
    if lib and os.path.isdir(os.path.join(lib, "models")):
        import upstream_adapter as ua
        theirs = ua.load_upstream("Yakopcic2013", lib)
        cc = ua.crosscheck(Yakopcic2013(**theirs.params), theirs, np.linspace(0.01, 0.99, 11), np.linspace(-1, 1, 11))
        check("upstream cross-check (Yakopcic2013)", cc["max_rel_dxdt"] < 1e-6 and cc["max_rel_i"] < 1e-9, f"rel dxdt {cc['max_rel_dxdt']:.1e}")
    elif not args.quiet:
        print("[SKIP] upstream cross-check — set MEMRISTEC_MODEL_LIBRARY to a local clone")

    print("verify_memristec: ALL CHECKS PASSED" if all_ok else "verify_memristec: FAILED")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
