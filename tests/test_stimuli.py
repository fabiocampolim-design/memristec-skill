# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
import numpy as np

from memristec_tools import STIMULI, rectangular, sine, triangular


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
