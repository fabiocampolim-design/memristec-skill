# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import glob
import json
import os
import subprocess
import sys

from conftest import ROOT

TOOLS = os.path.join(ROOT, "scripts", "memristec_tools.py")


def _run(args, cwd):
    return subprocess.run([sys.executable, TOOLS, *args], capture_output=True, text=True, cwd=cwd,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})


def test_version_prints_version_file():
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        ver = f.read().strip()
    p = _run(["--version"], ROOT)
    assert p.returncode == 0 and ver in p.stdout


def test_selftest_passes_and_writes_audit_log(tmp_path):
    p = _run(["--selftest", "--outdir", str(tmp_path / "out"), "--log-dir", str(tmp_path / "logs")], ROOT)
    assert p.returncode == 0, p.stdout + p.stderr
    logs = glob.glob(str(tmp_path / "logs" / "memristec_tools_*.json"))
    assert len(logs) == 1
    with open(logs[0], encoding="utf-8") as f:
        rec = json.load(f)
    assert rec["version"] and rec["argv"][0] == "--selftest" and rec["ok"] is True
    assert all(c["ok"] for c in rec["checks"])


def test_run_writes_csv_and_summary(tmp_path):
    p = _run(["--model", "yakopcic2013", "--stimulus", "sin", "--amplitude", "1.0",
              "--frequency", "1.0", "--cycles", "1", "--outdir", str(tmp_path / "out"),
              "--log-dir", str(tmp_path / "logs"), "-q"], ROOT)
    assert p.returncode == 0, p.stdout + p.stderr
    csvs = glob.glob(str(tmp_path / "out" / "yakopcic2013_sin_A1.0V_F1.0Hz.csv"))
    assert len(csvs) == 1
    with open(csvs[0], encoding="utf-8") as f:
        header = f.readline().strip()
    assert header == "t,v,i,x"


def test_usage_error_exit_code_2():
    p = _run(["--model", "nope"], ROOT)
    assert p.returncode == 2
