# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Minimal console + audit-file logger shared by the build scripts.

One record per invocation is appended to ``<log-dir>/<tool>.log``:
timestamp, exact command line, Python/package versions, every message at
INFO level or above, and the final outcome (exit code, wall time).
"""

import datetime as _dt
import os
import platform
import sys
import time


def _versions():
    out = [f"python {platform.python_version()} ({platform.system()})"]
    for name in ("numpy", "scipy", "matplotlib", "nbconvert"):
        try:
            mod = __import__(name)
            out.append(f"{name} {getattr(mod, '__version__', '?')}")
        except Exception:  # noqa: BLE001
            out.append(f"{name} (not importable)")
    return ", ".join(out)


class AuditLog:
    def __init__(self, tool, outdir, log_dir=None, verbose=False, quiet=False, dry=False):
        self.tool = tool
        self.verbose, self.quiet = verbose, quiet
        self.t0 = time.time()
        self.lines = []
        self.path = None
        if not dry:
            log_dir = log_dir or os.path.join(outdir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            self.path = os.path.join(log_dir, f"{tool}.log")
        stamp = _dt.datetime.now().isoformat(timespec="seconds")
        self._record(f"=== {tool} {stamp}")
        self._record("cmd: " + " ".join(sys.argv))
        self._record("cwd: " + os.getcwd())
        self._record("versions: " + _versions())

    # -- levels -------------------------------------------------------------
    def debug(self, msg):
        if self.verbose:
            print(msg)
        self._record("DEBUG " + msg)

    def info(self, msg):
        if not self.quiet:
            print(msg)
        self._record("INFO  " + msg)

    def warn(self, msg):
        print("WARNING:", msg, file=sys.stderr)
        self._record("WARN  " + msg)

    def error(self, msg):
        print("ERROR:", msg, file=sys.stderr)
        self._record("ERROR " + msg)

    # -- plumbing -----------------------------------------------------------
    def _record(self, line):
        self.lines.append(line)

    def close(self, rc):
        self._record(f"outcome: rc={rc} wall={time.time() - self.t0:.1f}s")
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write("\n".join(self.lines) + "\n\n")
            if self.verbose:
                print(f"audit log: {self.path}")
