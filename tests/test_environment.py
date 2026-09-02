# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""The environment the notebooks and tools are executed in."""

import sys


def test_python_is_312_or_newer():
    assert sys.version_info >= (3, 12)


def test_scientific_stack_imports_with_expected_floors():
    import numpy, scipy, matplotlib, yaml  # noqa: E401
    assert tuple(int(p) for p in numpy.__version__.split(".")[:2]) >= (2, 0)
    assert tuple(int(p) for p in scipy.__version__.split(".")[:2]) >= (1, 14)
    assert tuple(int(p) for p in matplotlib.__version__.split(".")[:2]) >= (3, 9)
    assert yaml.safe_load("a: 1") == {"a": 1}
