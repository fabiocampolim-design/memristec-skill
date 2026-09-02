# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Yakopcic et al. 2011 (IEEE EDL 32, 1436) / 2013 (IEEE TCAD 32, 1201).

  i = a1 x sinh(b v) for v >= 0, a2 x sinh(b v) for v < 0
  dx/dt = eta g(v) f(x, v), with the threshold function g and the
  boundary-decay function f of the 2013 paper (references/models.md).
"""

import numpy as np

from memristec_tools import Yakopcic2013, simulate


def test_no_state_motion_below_thresholds():
    m = Yakopcic2013()
    for v in np.linspace(-m.params["Vn"], m.params["Vp"], 9):
        assert m.state_derivative(0.5, v) == 0.0


def test_motion_direction_follows_voltage_sign_above_threshold():
    m = Yakopcic2013()
    assert m.state_derivative(0.5, 1.0) > 0.0
    assert m.state_derivative(0.5, -1.0) < 0.0


def test_current_is_odd_in_voltage_and_zero_at_origin():
    m = Yakopcic2013(a1=0.2, a2=0.2)
    assert m.current(0.4, 0.0) == 0.0
    assert np.isclose(m.current(0.4, 0.3), -m.current(0.4, -0.3))
    assert np.isclose(m.current(0.4, 0.3), 0.2 * 0.4 * np.sinh(0.05 * 0.3))


def test_boundary_functions_vanish_at_the_boundaries():
    m = Yakopcic2013()
    assert np.isclose(m.f(1.0, +1.0), 0.0)     # wp(1) = 0
    assert np.isclose(m.f(0.0, -1.0), 0.0)     # wn(0) = 0
    assert m.f(0.1, +1.0) == 1.0               # below xp: no decay


def test_sine_drive_keeps_state_in_unit_interval_and_loop_is_pinched():
    m = Yakopcic2013()
    t = np.linspace(0.0, 2.0, 8001)
    v = np.sin(2 * np.pi * 1.0 * t)
    res = simulate(m, t, v, method="rk4")
    assert 0.0 <= res.x.min() and res.x.max() <= 1.0
    assert np.isclose(res.i[0], 0.0) and np.isclose(res.i[4000], 0.0, atol=1e-9)
    assert res.x.max() > m.x0     # it actually switched
