# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import os
import subprocess
import sys

from conftest import ROOT

VERIFY = os.path.join(ROOT, "scripts", "verify_memristec.py")


def test_verify_passes_in_this_environment():
    p = subprocess.run([sys.executable, VERIFY], capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "MEMRISTEC_MODEL_LIBRARY": ""})
    assert p.returncode == 0, p.stdout + p.stderr
    assert "[PASS] imports" in p.stdout and "[SKIP] upstream cross-check" in p.stdout


def test_verify_quiet_prints_one_line():
    p = subprocess.run([sys.executable, VERIFY, "-q"], capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "MEMRISTEC_MODEL_LIBRARY": ""})
    assert p.returncode == 0 and len(p.stdout.strip().splitlines()) == 1
