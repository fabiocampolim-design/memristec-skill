# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Execute the chapter notebooks top-to-bottom and tally their inline checks.

This is the project's real regression suite: every physics claim in the
notebooks prints ``[PASS]``/``[FAIL]``; this script runs each chapter notebook
(``chapters/*.ipynb``, see ``build/assemble.py``) with nbconvert on the pinned
kernel, stores the outputs (in place by default) and counts PASS / FAIL /
error outputs. Exit code is non-zero if any FAIL, any error output, or an
nbconvert failure occurred.

Usage:
    python build/execute.py                        # every chapter, in place
    python build/execute.py --which main           # the book chapters (same as all)
    python build/execute.py --which 03             # one chapter (keys: assemble.py --list)
    python build/execute.py --outdir out/          # executed copies into out/chapters/, repo untouched
    python build/execute.py --tally-only           # just count what is already stored
    python build/execute.py --kernel memristec-mc --timeout 900 -v

Audit log: ``<log-dir>/execute.log`` (default ``<outdir>/logs``); nbconvert's own
output goes to ``<log-dir>/nbconvert-<notebook>.log``.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from buildlog import AuditLog  # noqa: E402
from assemble import BY_KEY, CHAPTERS_DIR, select  # noqa: E402


def tally(path):
    """Count PASS/FAIL markers, error outputs, figures and captions in a notebook."""
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    t = {"cells": len(nb["cells"]), "code": 0, "pass": 0, "fail": 0,
         "errors": 0, "figures": 0, "captions": 0, "unexecuted": 0, "fail_labels": []}
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        t["code"] += 1
        outs = c.get("outputs", [])
        if c.get("execution_count") is None and "".join(c["source"]).strip():
            t["unexecuted"] += 1          # executed cells carry a count even when silent
        for o in outs:
            if o.get("output_type") == "error":
                t["errors"] += 1
            text = "".join(o.get("text", [])) if isinstance(o.get("text"), list) else o.get("text", "")
            lines = [ln.strip() for ln in text.splitlines()]
            # only the check() marker at the start of a line counts: the tally cell's own
            # "search this notebook for '[FAIL]'" hint used to inflate the count by one
            t["pass"] += sum(1 for ln in lines if ln.startswith("[PASS]"))
            t["fail"] += sum(1 for ln in lines if ln.startswith("[FAIL]"))
            t["fail_labels"] += [ln for ln in lines if ln.startswith("[FAIL]")]
            data = o.get("data", {})
            if "image/png" in data:
                t["figures"] += 1
            html = "".join(data.get("text/html", [])) if "text/html" in data else ""
            if "<b>Figure" in html:
                t["captions"] += 1
    return t


def tally_series(paths):
    """Sum the tallies of several notebooks (a series of chapters)."""
    total = None
    for p in paths:
        t = tally(p)
        if total is None:
            total = t
            continue
        for k, v in t.items():
            total[k] = total[k] + v
    return total


def run_nbconvert(src, dst, kernel, timeout, log_dir):
    if os.path.abspath(src) != os.path.abspath(dst):
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(src, dst)
    cmd = [sys.executable, "-m", "nbconvert", "--to", "notebook", "--execute",
           "--inplace", dst, f"--ExecutePreprocessor.kernel_name={kernel}",
           f"--ExecutePreprocessor.timeout={timeout}"]
    # a copy executed under --outdir finds the toolkit through this variable (setup cell)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MEMRISTEC_SKILL_ROOT=ROOT)
    logfile = os.path.join(log_dir, f"nbconvert-{os.path.basename(dst)}.log")
    with open(logfile, "w", encoding="utf-8") as lf:
        proc = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(dst)) or ".",
                              stdout=lf, stderr=subprocess.STDOUT, env=env)
    return proc.returncode, logfile


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--which", default="all",
                    help="all (default), main, or one chapter key")
    ap.add_argument("--indir", default=ROOT,
                    help="repository root holding chapters/ (default: this repository)")
    ap.add_argument("--outdir", default=None,
                    help="write executed copies under <outdir>/chapters/ instead of in place")
    ap.add_argument("--log-dir", default=None, help="default: <outdir or indir>/logs")
    ap.add_argument("--kernel", default="memristec-mc", help="Jupyter kernel name (default memristec-mc)")
    ap.add_argument("--timeout", type=int, default=900, help="per-cell timeout in seconds")
    ap.add_argument("--tally-only", action="store_true",
                    help="do not execute; only count what the notebook files already contain")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("-v", "--verbose", action="store_true")
    g.add_argument("-q", "--quiet", action="store_true")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)

    outdir = args.outdir or args.indir
    os.makedirs(outdir, exist_ok=True)
    log_dir = args.log_dir or os.path.join(outdir, "logs")
    log = AuditLog("execute", outdir, log_dir, verbose=args.verbose, quiet=args.quiet)
    rc = 0
    t_all = time.time()
    totals = {}
    try:
        keys = select(args.which)
    except SystemExit as exc:          # an unknown --which is still an audited failure
        log.error(str(exc))
        log.close(2)
        return 2
    for key in keys:
        ch = BY_KEY[key]
        src = os.path.join(args.indir, CHAPTERS_DIR, ch.file)
        dst = os.path.join(outdir, CHAPTERS_DIR, ch.file)
        if not os.path.exists(src):
            log.error(f"missing {src}")
            rc = 1
            continue
        if not args.tally_only:
            t0 = time.time()
            code, logfile = run_nbconvert(src, dst, args.kernel, args.timeout, log_dir)
            log.info(f"{ch.file}: nbconvert rc={code} in {time.time() - t0:.0f}s (log: {logfile})")
            if code != 0:
                rc = 1
        elif not os.path.exists(dst):
            dst = src                  # --tally-only --outdir: count the source copy
        t = tally(dst)
        totals.setdefault("book", []).append(t)
        log.info(f"{ch.file}: {t['cells']} cells ({t['code']} code) | "
                 f"PASS {t['pass']} FAIL {t['fail']} errors {t['errors']} | "
                 f"figures {t['figures']} captions {t['captions']} | "
                 f"unexecuted code cells {t['unexecuted']}")
        for lbl in t["fail_labels"]:
            log.warn(lbl)
        if t["fail"] or t["errors"] or t["unexecuted"]:
            rc = 1
    for series, ts in totals.items():
        log.info(f"{series}: {len(ts)} notebooks | PASS {sum(t['pass'] for t in ts)} "
                 f"FAIL {sum(t['fail'] for t in ts)} | figures {sum(t['figures'] for t in ts)} "
                 f"captions {sum(t['captions'] for t in ts)}")
    log.info(f"RESULT: {'OK' if rc == 0 else 'PROBLEMS — see above'} ({time.time() - t_all:.0f} s)")
    log.close(rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
