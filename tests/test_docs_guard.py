# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Playbook rule 15: the suite guards the docs — every CLI flag is documented
in AGENTS.md and docs/USER_MANUAL.md; VERSION, CITATION and CHANGELOG agree;
SKILL.md points at existing reference files."""

import os
import re

import pytest

from conftest import ROOT


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def _flags(parser):
    return {s for a in parser._actions for s in a.option_strings if s.startswith("--") and s != "--help"}


@pytest.mark.parametrize("module", ["memristec_tools", "upstream_adapter", "verify_memristec"])
def test_script_flags_are_documented(module):
    mod = __import__(module)
    agents, manual = _read("AGENTS.md"), _read("docs", "USER_MANUAL.md")
    for f in _flags(mod.build_parser()):
        assert f in agents, f"{module}: {f} missing from AGENTS.md"
        assert f in manual, f"{module}: {f} missing from docs/USER_MANUAL.md"


def test_version_citation_changelog_agree():
    ver = _read("VERSION").strip()
    assert f'version: "{ver}"' in _read("CITATION.cff")
    assert re.search(rf"^## {re.escape(ver)}\b", _read("CHANGELOG.md"), re.M)
    assert f"memristec-skill {ver}" in _read("SKILL.md")


def test_skill_references_exist():
    skill = _read("SKILL.md")
    refs = set(re.findall(r"references/([\w\-]+\.md)", skill))
    assert refs, "SKILL.md must point at reference files"
    for r in refs:
        assert os.path.isfile(os.path.join(ROOT, "references", r)), r


def test_models_reference_covers_every_registered_model():
    from memristec_tools import MODELS
    text = _read("references", "models.md")
    for name in MODELS:
        assert f"`{name}`" in text, name
