# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Shared fixtures. Run from memristec-skill/:  python -m pytest tests"""

import os
import sys

import pytest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))


def pytest_addoption(parser):
    parser.addoption("--run-notebooks", action="store_true", default=False,
                     help="re-execute every chapter notebook on the pinned kernel (slow)")


@pytest.fixture(scope="session")
def repo_root():
    return ROOT
