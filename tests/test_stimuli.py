# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import numpy as np

from memristec_tools import STIMULI, pulse_train, rectangular, sine, triangular


def test_sine_amplitude_and_period():
    t = np.linspace(0, 1, 1001)
    v = sine(t, 2.0, 1.0)
    assert np.isclose(v.max(), 2.0, atol=1e-6) and np.isclose(v[250], 2.0, atol=1e-6)
    assert np.isclose(v[0], 0.0) and np.isclose(v[500], 0.0, atol=1e-9)


def test_triangular_peaks_and_zero_crossings():
    t = np.linspace(0, 1, 1001)
    v = triangular(t, 1.0, 1.0)
    assert np.isclose(v.max(), 1.0) and np.isclose(v.min(), -1.0)
    assert np.isclose(v[0], -1.0)          # same convention as MemrisTec's FunctionGenerator
    assert np.isclose(v[500], 1.0)


def test_rectangular_levels_and_duty():
    t = np.linspace(0, 1, 1000, endpoint=False)
    v = rectangular(t, 3.0, 1.0, duty=0.25)
    assert set(np.unique(v)) == {3.0, -3.0}
    assert np.isclose((v > 0).mean(), 0.25, atol=1e-3)


def test_registry_names():
    assert set(STIMULI) == {"sin", "triangular", "rectangular"}


def test_pulse_train_levels_count_and_timing():
    t = np.linspace(0.0, 1.0, 10001)                      # dt = 1e-4
    v = pulse_train(t, 0.5, width=0.02, period=0.05, n_pulses=10)
    assert set(np.unique(v)) == {0.0, 0.5}
    on = v > 0
    assert abs(on.sum() - 2000) <= 20                      # 10 x 20 ms high, ±1 sample per edge
    assert v[0] == 0.5 and v[int(0.03 / 1e-4)] == 0.0 and v[int(0.05 / 1e-4)] == 0.5
    assert not on[int(0.5 / 1e-4) + 5:].any()             # nothing after the 10th period


def test_pulse_train_edges_are_consistent_on_an_exact_grid():
    """Every pulse of a train whose edges fall on grid points has the same
    number of samples (chapter 5 §18: round-off in t/period used to move an
    edge by one sample for some pulses only, so identical pulses moved the
    state by different amounts)."""
    t = np.linspace(0.0, 1.2, 24001)                      # dt = 5e-5; 0.02 / dt = 400 exactly
    v = pulse_train(t, -0.5, width=0.01, period=0.02, n_pulses=60)
    per_pulse = [int(np.sum(v[k * 400:(k + 1) * 400] != 0.0)) for k in range(60)]
    assert per_pulse == [200] * 60, sorted(set(per_pulse))
    assert v[0] != 0.0 and v[200] == 0.0 and v[400] != 0.0     # on at k*period, off at k*period + width


def test_pulse_train_offset_and_baseline():
    t = np.linspace(0.0, 1.0, 1001)
    v = pulse_train(t, -1.0, width=0.1, period=0.2, n_pulses=2, t0=0.3, baseline=0.05)
    assert v[0] == 0.05 and v[300] == -1.0 and v[450] == 0.05 and v[500] == -1.0 and v[800] == 0.05
