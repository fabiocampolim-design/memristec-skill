# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""S4 confidence infrastructure: our clean-room models against a *local* clone
of the MemrisTec Model Library (never shipped). Skips when
MEMRISTEC_MODEL_LIBRARY is unset. The tolerances live in
tests/records/crosscheck_v1.json (schema 1) so a drift on either side is visible.
"""

import json
import os

import numpy as np
import pytest

from conftest import ROOT
from memristec_tools import LinearIonDrift, StanfordPKU2016, VTEAM2015, Yakopcic2013
import upstream_adapter as ua

RECORDS = os.path.join(ROOT, "tests", "records", "crosscheck_v1.json")
LIB = ua.find_library()
needs_lib = pytest.mark.skipif(LIB is None, reason="MEMRISTEC_MODEL_LIBRARY not set")


def _records():
    with open(RECORDS, encoding="utf-8") as f:
        rec = json.load(f)
    assert rec["schema"] == 1
    return rec


def test_find_library_reads_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMRISTEC_MODEL_LIBRARY", str(tmp_path))
    assert ua.find_library() is None          # a directory without models/ is not a clone
    (tmp_path / "models").mkdir()
    assert ua.find_library() == str(tmp_path)
    monkeypatch.delenv("MEMRISTEC_MODEL_LIBRARY")
    assert ua.find_library() is None


def test_records_file_lists_every_shim():
    rec = _records()
    assert set(rec["models"]) == set(ua.SHIMS)


@needs_lib
def test_hp_biolek2009_folder_matches_our_joglekar_window_not_biolek():
    """P-1: the upstream folder named Biolek implements the Joglekar window."""
    theirs = ua.load_upstream("HP_Biolek2009", LIB)
    ours_j = LinearIonDrift(window="joglekar", **theirs.params)
    ours_b = LinearIonDrift(window="biolek", **theirs.params)
    x = np.linspace(0.02, 0.98, 25)
    v = np.linspace(-1.2, 1.2, 13)
    tol = _records()["models"]["HP_Biolek2009"]
    rj = ua.crosscheck(ours_j, theirs, x, v)
    rb = ua.crosscheck(ours_b, theirs, x, v)
    assert rj["max_rel_dxdt"] <= tol["max_rel_dxdt"] and rj["max_rel_i"] <= tol["max_rel_i"]
    assert rb["max_rel_dxdt"] > 0.1      # the true Biolek window differs by order one near the ends


@needs_lib
def test_yakopcic2013_matches_upstream_derivative_and_current():
    theirs = ua.load_upstream("Yakopcic2013", LIB)
    ours = Yakopcic2013(**theirs.params)
    tol = _records()["models"]["Yakopcic2013"]
    r = ua.crosscheck(ours, theirs, np.linspace(0.01, 0.99, 25), np.linspace(-1.0, 1.0, 21))
    assert r["max_rel_dxdt"] <= tol["max_rel_dxdt"] and r["max_rel_i"] <= tol["max_rel_i"]
    tr = ua.trajectory_crosscheck(ours, theirs, amplitude=1.0, frequency=1.0, cycles=1)
    assert tr["max_abs_x"] <= tol["max_abs_x_traj"]


@needs_lib
def test_vteam2015_matches_upstream_after_state_normalisation():
    theirs = ua.load_upstream("VTEAM2015", LIB)
    ours = VTEAM2015(**theirs.params)
    tol = _records()["models"]["VTEAM2015"]
    v = np.concatenate([np.linspace(-1.0, -0.35, 8), np.linspace(0.35, 1.0, 8)])   # outside the dead band
    r = ua.crosscheck(ours, theirs, np.linspace(0.02, 0.98, 25), v)
    assert r["max_rel_dxdt"] <= tol["max_rel_dxdt"] and r["max_rel_i"] <= tol["max_rel_i"]
    for vv in np.linspace(theirs.params["v_on"], theirs.params["v_off"], 5):          # dead band: both zero
        assert ours.state_derivative(0.5, vv) == 0.0 == theirs.state_derivative(0.5, vv)
    tr = ua.trajectory_crosscheck(ours, theirs, amplitude=0.3, frequency=100.0, cycles=1, n_per_cycle=4000)
    assert tr["max_abs_x"] <= tol["max_abs_x_traj"]


@needs_lib
def test_stanford_pku_matches_upstream_gap_dynamics_and_current():
    theirs = ua.load_upstream("Stanford_PKU", LIB)
    ours = StanfordPKU2016(**theirs.params)
    tol = _records()["models"]["Stanford_PKU"]
    r = ua.crosscheck(ours, theirs, np.linspace(0.01, 0.99, 25), np.linspace(-1.5, 1.5, 21))
    assert r["max_rel_dxdt"] <= tol["max_rel_dxdt"] and r["max_rel_i"] <= tol["max_rel_i"]
