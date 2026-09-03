# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Kvatinsky, Ramadan, Friedman, Kolodny 2015, IEEE TCAS-II 62(8), 786 — VTEAM.

  dx/dt = k_off (v/v_off - 1)^alpha_off f(x)   for v > v_off > 0
        = k_on  (v/v_on  - 1)^alpha_on  f(x)   for v < v_on  < 0
        = 0                                    otherwise
  i     = v / [R_on + (R_off - R_on) x]        (linear w-dependence, paper eq. 3)
x = (w - w_on)/(w_off - w_on); x = 0 is R_on. f is the rectangular window (1 inside (0, 1)).
"""

import numpy as np

from memristec_tools import MODELS, VTEAM2015, dynamic_route_map, iv_sweep, loop_metrics, pulse_response


def test_registered_and_defaults_have_the_paper_signs():
    assert MODELS["vteam2015"] is VTEAM2015
    m = VTEAM2015()
    assert m.params["k_off"] > 0 > m.params["k_on"]
    assert m.params["v_off"] > 0 > m.params["v_on"]


def test_dead_zone_between_thresholds():
    m = VTEAM2015()
    for v in np.linspace(m.params["v_on"], m.params["v_off"], 13):
        assert m.state_derivative(0.5, v) == 0.0


def test_rate_law_above_threshold():
    m = VTEAM2015(k_off=10.0, v_off=0.3, alpha_off=3.0, k_on=-10.0, v_on=-0.3, alpha_on=3.0)
    assert np.isclose(m.state_derivative(0.5, 0.6), 10.0 * (0.6 / 0.3 - 1.0) ** 3)     # = 10
    assert np.isclose(m.state_derivative(0.5, -0.6), -10.0 * (-0.6 / -0.3 - 1.0) ** 3)  # = -10
    assert m.state_derivative(0.5, 0.9) > m.state_derivative(0.5, 0.6)                   # superlinear


def test_resistance_is_linear_in_x_and_x0_is_R_on():
    m = VTEAM2015(R_on=1e3, R_off=1e5)
    assert np.isclose(m.resistance(0.0), 1e3) and np.isclose(m.resistance(1.0), 1e5)
    assert np.isclose(m.current(0.5, 0.1), 0.1 / 50500.0)


def test_rectangular_window_stops_at_the_boundaries_but_lets_the_state_leave_them():
    m = VTEAM2015()
    assert m.state_derivative(1.0, 0.6) == 0.0 and m.state_derivative(0.0, -0.6) == 0.0
    assert m.state_derivative(1.0, -0.6) < 0.0 and m.state_derivative(0.0, 0.6) > 0.0
    free = VTEAM2015(window=0)
    assert free.state_derivative(1.0, 0.6) > 0.0                    # no window: the driver clips


def test_sine_sweep_switches_fully_and_the_loop_is_pinched():
    res = iv_sweep(VTEAM2015(), 0.6, 1.0, cycles=2, n_per_cycle=2000)
    met = loop_metrics(res)
    assert met["pinched_at_origin"] and met["area"] > 1e-5           # measured 2.5e-4 V·A
    assert res.x.min() == 0.0 and res.x.max() == 1.0
    assert np.isclose(met["r_min"], 1e3) and np.isclose(met["r_max"], 1e5)


def test_drm_has_a_dead_band_and_the_paper_sign():
    drm = dynamic_route_map(VTEAM2015(), np.linspace(0, 1, 11), [-0.6, -0.3, 0.0, 0.3, 0.6])
    assert drm[-0.6][5] == -10.0 and drm[0.6][5] == 10.0
    assert all(drm[v][5] == 0.0 for v in (-0.3, 0.0, 0.3))


def test_positive_pulses_raise_x_gradually_towards_R_off():
    pr = pulse_response(VTEAM2015(x0=0.2), 0.5, width=0.02, period=0.05, n_pulses=20)
    assert np.all(np.diff(pr["x_after"]) >= 0) and pr["x_after"][-1] == 1.0
    assert 0.25 < pr["x_after"][0] < 0.27                             # measured 0.259
    assert pr["G_after"][0] > pr["G_after"][-1]                       # x up = conductance down
