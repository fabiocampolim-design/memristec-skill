# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Jiang et al. 2016, IEEE Trans. Electron Devices 63(5), 1884 — Stanford–PKU RRAM model.

  i     = I0 exp(-g/g0) sinh(v/V0)
  dg/dt = -nu0 exp(-Ea/kT) sinh(gamma (a0/t_ox) q v / kT),  gamma = gamma0 - beta (g/1 nm)^alpha
  T     = T0 + |v i| R_th
x = (g_max - g)/(g_max - g_min): x = 1 is the smallest gap (LRS).
"""

import math

import numpy as np

from memristec_tools import K_B, MODELS, Q_E, StanfordPKU2016, iv_sweep, loop_metrics, simulate


def test_registered_and_gap_mapping():
    assert MODELS["stanford_pku2016"] is StanfordPKU2016
    m = StanfordPKU2016()
    assert np.isclose(m.gap(0.0), m.params["g_max"]) and np.isclose(m.gap(1.0), m.params["g_min"])


def test_current_law_and_odd_symmetry():
    m = StanfordPKU2016(I0=1e-4, g0=0.25e-9, V0=0.25)
    g = m.gap(0.3)
    assert np.isclose(m.current(0.3, 0.2), 1e-4 * math.exp(-g / 0.25e-9) * math.sinh(0.8))
    assert np.isclose(m.current(0.3, 0.2), -m.current(0.3, -0.2))
    assert m.current(0.3, 0.0) == 0.0
    assert m.current(1.0, 0.1) > m.current(0.0, 0.1)                 # smaller gap, more current


def test_temperature_rises_with_dissipated_power_and_never_drops_below_T0():
    m = StanfordPKU2016()
    assert m.temperature(0.5, 0.0) == m.params["T0"]
    assert m.temperature(1.0, 1.0) > m.temperature(1.0, 0.1) > m.params["T0"]
    assert m.temperature(1.0, -1.0) == m.temperature(1.0, 1.0)      # |v i| is even


def test_gap_rate_law_at_room_temperature_without_self_heating():
    m = StanfordPKU2016(R_th=0.0, nu0=10.0, Ea=0.6, gamma0=16.0, beta=0.0)
    T = m.params["T0"]
    v = 0.5
    arg = 16.0 * (m.params["a0"] / m.params["t_ox"]) * Q_E * v / (K_B * T)
    expected = -10.0 * math.exp(-0.6 * Q_E / (K_B * T)) * math.sinh(arg)
    assert np.isclose(m.gap_rate(0.5, v), expected)
    assert m.state_derivative(0.5, v) > 0.0 > m.state_derivative(0.5, -v)   # + closes the gap


def test_bipolar_loop_sets_at_about_one_volt_at_1_kHz_and_resets_on_the_negative_branch():
    m = StanfordPKU2016()
    n = 20000
    res = iv_sweep(m, 1.5, 1e3, cycles=1, n_per_cycle=n)
    q = n // 4
    up = res.x[:q]
    v_set = res.v[int(np.argmax(up > 0.5))]
    assert 0.9 < v_set < 1.3                                          # measured 1.08 V
    assert res.x[q] == 1.0 and res.x[3 * q] == 0.0 and res.x[-1] == 0.0
    met = loop_metrics(res)
    assert met["pinched_at_origin"] and met["i_max"] > 1e-3           # measured 4.1 mA
    assert 0.1 / m.current(0.0, 0.1) > 100 * (0.1 / m.current(1.0, 0.1))   # HRS/LRS > 100 (measured 180)


def test_set_voltage_drops_for_a_slower_sweep():
    def v_set(freq):
        n = 20000
        res = iv_sweep(StanfordPKU2016(), 1.5, freq, cycles=1, n_per_cycle=n)
        return res.v[int(np.argmax(res.x[: n // 4] > 0.5))]
    assert v_set(1.0) < v_set(1e3) < v_set(1e5)                       # measured 0.47 / 1.08 / 1.45 V


def test_state_stays_in_unit_interval_under_a_zero_bias_hold():
    m = StanfordPKU2016(x0=0.7)
    t = np.linspace(0.0, 1e-3, 1001)
    res = simulate(m, t, np.zeros_like(t))
    assert np.allclose(res.x, 0.7)                                    # no retention loss in this model
