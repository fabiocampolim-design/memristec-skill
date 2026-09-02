# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Linear ion drift (Strukov 2008) with the three classical windows.

Physics checked here, not just code:
  * R(x) interpolates R_on..R_off; i = v / R(x).
  * Without a window, memristance is an affine function of charge:
    M(q) = R_off - (R_off - R_on) * k * q,  k = mu_v R_on / D^2  (Strukov eq. 6).
  * Joglekar window vanishes at both boundaries and is 1 at x = 1/2.
  * Biolek window depends on the current sign: f(x, i>0) -> 0 only at x = 1,
    f(x, i<0) -> 0 only at x = 0 (the "terminal state" fix, Biolek 2009 eq. 8).
  * Prodromakis window is j at x = 1/2 for p -> large and never negative on [0, 1].
"""

import numpy as np
import pytest

from memristec_tools import LinearIonDrift, simulate


def test_resistance_and_current():
    m = LinearIonDrift(window="none", R_on=100.0, R_off=16e3)
    assert np.isclose(m.resistance(0.0), 16e3) and np.isclose(m.resistance(1.0), 100.0)
    assert np.isclose(m.current(0.5, 1.0), 1.0 / (0.5 * 100.0 + 0.5 * 16e3))


def test_unknown_parameter_is_refused():
    with pytest.raises(ValueError):
        LinearIonDrift(window="none", Ron=100.0)


def test_unknown_window_is_refused():
    with pytest.raises(ValueError):
        LinearIonDrift(window="hann")


def test_memristance_is_affine_in_charge_without_window():
    m = LinearIonDrift(window="none", x0=0.5)
    k = m.params["mu_v"] * m.params["R_on"] / m.params["D"] ** 2
    t = np.linspace(0.0, 1.0, 20001)
    v = 0.05 * np.sin(2 * np.pi * 5.0 * t)          # small: x stays inside (0, 1)
    res = simulate(m, t, v, method="rk4")
    assert res.x.min() > 0.0 and res.x.max() < 1.0
    q = np.concatenate([[0.0], np.cumsum(0.5 * (res.i[1:] + res.i[:-1]) * np.diff(t))])
    mask = np.abs(res.v) > 1e-3 * np.abs(res.v).max()      # never divide at a zero crossing
    M = res.v[mask] / res.i[mask]
    slope, intercept = np.polyfit(q[mask], M, 1)
    expected_slope = -(m.params["R_off"] - m.params["R_on"]) * k
    assert np.isclose(slope, expected_slope, rtol=1e-3)
    assert np.isclose(intercept, m.resistance(0.5), rtol=1e-4)


@pytest.mark.parametrize("window", ["joglekar", "biolek", "prodromakis"])
def test_window_is_within_unit_interval(window):
    m = LinearIonDrift(window=window, p=10)
    for x in np.linspace(0, 1, 11):
        for i in (-1e-3, 1e-3):
            f = m.window_value(x, i)
            assert -1e-12 <= f <= 1.0 + 1e-12


def test_joglekar_vanishes_at_both_ends_and_peaks_at_half():
    m = LinearIonDrift(window="joglekar", p=10)
    assert np.isclose(m.window_value(0.0, 1e-3), 0.0)
    assert np.isclose(m.window_value(1.0, 1e-3), 0.0)
    assert np.isclose(m.window_value(0.5, 1e-3), 1.0)


def test_biolek_window_depends_on_current_sign():
    m = LinearIonDrift(window="biolek", p=10)
    assert np.isclose(m.window_value(1.0, +1e-3), 0.0)   # stuck-at-1 only while pushing up
    assert np.isclose(m.window_value(1.0, -1e-3), 1.0)   # free to leave x = 1 when i < 0
    assert np.isclose(m.window_value(0.0, -1e-3), 0.0)
    assert np.isclose(m.window_value(0.0, +1e-3), 1.0)


def test_prodromakis_window_center_value():
    m = LinearIonDrift(window="prodromakis", p=1, j=1.0)
    # j * (1 - [(x-0.5)^2 + 0.75]^p) at x = 0.5, p = 1 -> 0.25
    assert np.isclose(m.window_value(0.5, 1e-3), 0.25)


def test_state_stays_bounded_under_large_sine_for_each_window():
    t = np.linspace(0.0, 2.0, 4001)
    v = 1.2 * np.sin(2 * np.pi * 1.0 * t)
    for window in ("none", "joglekar", "biolek", "prodromakis"):
        res = simulate(LinearIonDrift(window=window, R_off=38e3, mu_v=1e-14, x0=0.26), t, v, method="rk4")
        assert res.x.min() >= 0.0 and res.x.max() <= 1.0, window
        assert np.isclose(res.i[0], 0.0)
