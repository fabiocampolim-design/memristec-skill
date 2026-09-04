# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
from nbbuild import md, code

# Chapter 0. ``__CHAPTER_LIST__`` is filled in by build/assemble.py.
CELLS = [
md(r"""
# MemrisTec Compact Models — Memristor Physics from Paper to Code

**An executed tour of the compact memristor models behind the MemrisTec Model Library — every
equation transcribed from its paper, every figure generated live, every claim checked.**

A memristor is a two-terminal device whose resistance depends on an internal state that its own
current or voltage history drives. The MemrisTec platform (DFG priority programme SPP 2262)
collects compact models of such devices in a Model Library. This book re-derives the families
that have a published equation set — the linear ion drift model with its window functions, the
VTEAM threshold model, the Stanford–PKU filamentary model and the Yakopcic device model — from
the papers, runs them through one shared ODE driver (`scripts/memristec_tools.py`), and compares
them with the library through an optional adapter that reads *your* local clone. No line of the
library is in this repository; `references/models.md` records the source of every equation.

The book is shipped as **one notebook per chapter** (this folder); each runs on its own.
Section numbers (§1–26), figure numbers and cross-references are global, so "§14" means section
14 wherever it lives.

**Contents**

__CHAPTER_LIST__

### How to run this

One-time setup (Windows / miniconda; a `.sh` twin exists for Linux and macOS):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_memristec_windows.ps1
```

This creates the conda env `memristec` (Python 3.12, numpy 2, scipy, matplotlib, nbconvert) and
registers the Jupyter kernel **`Python 3.12 (memristec)`** (`memristec-mc`) that every chapter
is pinned to. Verify with `python scripts/verify_memristec.py`. Running all chapters top to
bottom takes about a minute on a laptop; no cell needs more than ~15 s. The last cell of this
chapter is the setup cell every chapter starts with — run it here to check the kernel.

To compare with the MemrisTec Model Library, set `MEMRISTEC_MODEL_LIBRARY` to a local clone
before starting Jupyter (chapter 6, §24); the cells that need it say so and print `[SKIP]`
when the variable is unset.
"""),

md(r"""
### Conventions used throughout

- **State.** Every model has one state variable $x \in [0, 1]$. For the linear ion drift and
  Stanford–PKU models $x = 1$ is the low-resistance state; for VTEAM $x = 0$ is $R_{\rm on}$
  (the paper's variable, kept as published — chapter 3 explains). Compare *conductances*
  across models, never $x$.
- **Sign.** A positive voltage drives the linear ion drift and Stanford–PKU models towards low
  resistance (SET) and VTEAM towards high resistance (RESET, the paper's $k_{\rm off}$ branch).
- **Units.** SI throughout: volts, amperes, seconds, metres, kelvin. Rates of the normalised
  state are in s⁻¹.
- **Driver.** `simulate(model, t, v, method)` integrates $\dot x = f(x, v(t))$ on the given grid
  (fixed-step RK4 by default) and clips $x$ to $[0, 1]$; `iv_sweep` builds the grid for a
  periodic stimulus; `loop_metrics` measures the pinched loop; `dynamic_route_map` tabulates
  $\dot x(x)$ at fixed voltages; `pulse_response` reads the state after each pulse of a train.
- Every section that makes a quantitative claim ends with an inline check that prints **PASS**
  or **FAIL**. A clean run has zero FAILs; the last cell of every chapter counts them.
"""),
]

# The setup cell every chapter starts with. build/assemble.py substitutes
# ``__FIG_OFFSET__`` and ``__CHAPTER__``.
SETUP_TEMPLATE = r"""
# ---- shared setup: this cell is identical in every chapter of the book ----------
import os
import sys
import time
import warnings

import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, HTML

# the toolkit lives in scripts/ at the repository root (chapters/ is one level down);
# build/execute.py --outdir runs a copy elsewhere and names the root in MEMRISTEC_SKILL_ROOT
for _cand in ("scripts", os.path.join("..", "scripts"),
              os.path.join(os.environ.get("MEMRISTEC_SKILL_ROOT", ""), "scripts")):
    if os.path.isfile(os.path.join(_cand, "memristec_tools.py")):
        sys.path.insert(0, os.path.abspath(_cand))
        break
import memristec_tools as mt
from memristec_tools import (LinearIonDrift, Yakopcic2013, VTEAM2015, StanfordPKU2016, MODELS,
                             simulate, iv_sweep, loop_metrics, dynamic_route_map,
                             pulse_train, pulse_response, sine, triangular, rectangular)

plt.rcParams.update({"figure.dpi": 100, "figure.figsize": (7.0, 4.0), "axes.grid": True,
                     "grid.alpha": 0.3, "font.size": 10})
warnings.filterwarnings("ignore", category=RuntimeWarning)

_CHECKS = {"pass": 0, "fail": 0}
_FIG = {"n": __FIG_OFFSET__}               # figure numbers run through the whole book

def check(label, ok, detail=""):
    '''Inline physics check; prints PASS/FAIL and tallies for the final summary.'''
    ok = bool(ok)
    _CHECKS["pass" if ok else "fail"] += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return ok

def caption(text):
    '''Numbered caption rendered directly below the figure it describes.'''
    _FIG["n"] += 1
    display(HTML(
        f"<div style='max-width:780px;margin:2px 0 14px 12px;font-size:0.92em;"
        f"color:#444;border-left:3px solid #bbb;padding-left:10px'>"
        f"<b>Figure {_FIG['n']}.</b> {text}</div>"))

def show(fig):
    '''Display a figure and close it (keeps the notebook small).'''
    plt.show()
    plt.close(fig)

print("memristec-skill", mt.__version__, "| numpy", np.__version__, "| __CHAPTER__")
t_chapter_start = time.time()
"""


def setup_cell(label, fig_offset):
    return code(SETUP_TEMPLATE.replace("__FIG_OFFSET__", str(fig_offset)).replace("__CHAPTER__", label))
