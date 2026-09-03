# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import numpy as np
import pytest

from memristec_tools import (LinearIonDrift, Yakopcic2013, dynamic_route_map,
                             iv_sweep, loop_metrics, make_model, pulse_response, simulate)


def test_make_model_registry():
    assert isinstance(make_model("yakopcic2013"), Yakopcic2013)
    with pytest.raises(ValueError):
        make_model("hp_2008")


def test_methods_agree_on_a_smooth_problem():
    m = LinearIonDrift(window="joglekar", x0=0.3)
    t = np.linspace(0, 1, 4001)
    v = 1.0 * np.sin(2 * np.pi * t)
    xr = simulate(m, t, v, "rk4").x
    xe = simulate(m, t, v, "euler").x
    xi = simulate(m, t, v, "ivp").x
    assert np.max(np.abs(xr - xi)) < 1e-4
    assert np.max(np.abs(xr - xe)) < 1e-2


def test_simulate_rejects_bad_shapes():
    m = LinearIonDrift()
    with pytest.raises(ValueError):
        simulate(m, np.linspace(0, 1, 5), np.zeros(4))
    with pytest.raises(ValueError):
        simulate(m, np.linspace(0, 1, 5), np.zeros(5), method="magic")


def test_iv_sweep_shape_and_pinched_loop():
    res = iv_sweep(LinearIonDrift(window="biolek", R_off=38e3, x0=0.26),
                   amplitude=1.2, frequency=1.0, cycles=2, n_per_cycle=1000)
    assert len(res.t) == 2001 and np.isclose(res.t[-1], 2.0)
    met = loop_metrics(res)
    assert met["pinched_at_origin"]
    assert met["area"] > 0.0
    assert met["r_min"] < met["r_max"]
    assert met["i_max"] > 0 > met["i_min"]


def test_loop_area_is_zero_for_a_pure_resistor():
    m = LinearIonDrift(window="none", mu_v=0.0)     # no state motion -> straight line
    res = iv_sweep(m, 1.0, 1.0, cycles=1, n_per_cycle=1000)
    assert np.isclose(loop_metrics(res)["area"], 0.0, atol=1e-12)


def test_loop_area_counts_both_lobes_of_a_symmetric_pinched_loop():
    res = iv_sweep(LinearIonDrift(window="none"), 1.0, 1.0, cycles=1, n_per_cycle=4000)
    met = loop_metrics(res)
    assert met["area"] > 1e-6                    # measured 1.79e-5 V·A
    assert abs(met["area_signed"]) < 1e-12       # the lobes cancel in the signed sum
    assert met["pinched_at_origin"]


def test_loop_area_of_a_resistor_is_zero():
    class R(LinearIonDrift):
        def state_derivative(self, x, v):
            return 0.0
    res = iv_sweep(R(window="none"), 1.0, 1.0, cycles=1, n_per_cycle=1000)
    assert loop_metrics(res)["area"] < 1e-15


def test_pulse_response_positive_pulses_raise_state_and_conductance():
    pr = pulse_response(LinearIonDrift(window="joglekar", x0=0.2), 1.0, width=0.02, period=0.05, n_pulses=10)
    assert pr["x_after"].shape == (10,) and pr["G_after"].shape == (10,)
    assert np.all(np.diff(pr["x_after"]) > 0) and np.all(np.diff(pr["G_after"]) > 0)
    assert len(pr["t"]) == 10 * 400 + 1 and np.isclose(pr["t"][-1], 0.5)
    assert pr["v"].max() == 1.0 and pr["v"].min() == 0.0


def test_dynamic_route_map_signs():
    m = Yakopcic2013()
    drm = dynamic_route_map(m, np.linspace(0, 1, 21), [-1.0, 0.0, 1.0])
    assert set(drm) == {-1.0, 0.0, 1.0}
    assert np.all(drm[0.0] == 0.0)
    assert np.all(drm[1.0][1:-1] > 0.0) and np.all(drm[-1.0][1:-1] < 0.0)
    assert np.isclose(drm[1.0][-1], 0.0) and np.isclose(drm[-1.0][0], 0.0)
