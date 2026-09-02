# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Shared fixtures. Run from memristec-skill/:  python -m pytest tests"""

import os
import sys

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


@pytest.fixture(scope="session")
def repo_root():
    return ROOT
