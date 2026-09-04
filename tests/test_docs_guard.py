# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Playbook rule 15: the suite guards the docs — every CLI flag is documented
in AGENTS.md and docs/USER_MANUAL.md; VERSION, CITATION and CHANGELOG agree;
SKILL.md points at existing reference files."""

import os
import re
import sys

import pytest

from conftest import ROOT

sys.path.insert(0, os.path.join(ROOT, "build"))
sys.path.insert(0, os.path.join(ROOT, "docs"))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as f:
        return f.read()


def _flags(parser):
    return {s for a in parser._actions for s in a.option_strings if s.startswith("--") and s != "--help"}


def test_build_manual_writes_html_without_pandoc(tmp_path, monkeypatch):
    """Rule 10: the manual builds from the Markdown even on a machine without pandoc."""
    import build_manual
    monkeypatch.setattr(build_manual.shutil, "which", lambda name: None)
    assert build_manual.main(["--outdir", str(tmp_path), "--no-pdf"]) == 0
    out = (tmp_path / "USER_MANUAL.html").read_text(encoding="utf-8")
    assert "<title>memristec-skill" in out and "<h2>" in out and "<table>" in out
    assert "scripts/watch_upstream.py" in out                   # the manual's own content came through


@pytest.mark.parametrize("module", ["memristec_tools", "upstream_adapter", "verify_memristec", "watch_upstream", "assemble", "execute", "build_manual"])
def test_script_flags_are_documented(module):
    mod = __import__(module)
    agents, manual = _read("AGENTS.md"), _read("docs", "USER_MANUAL.md")
    for f in _flags(mod.build_parser()):
        assert f in agents, f"{module}: {f} missing from AGENTS.md"
        assert f in manual, f"{module}: {f} missing from docs/USER_MANUAL.md"


@pytest.mark.parametrize("module", ["memristec_tools", "upstream_adapter"])
def test_flag_choices_are_documented(module):
    """Finding N-3: the flag names were guarded but their choices were not, and
    AGENTS.md / the manual still listed two models after four shipped."""
    mod = __import__(module)
    agents, manual = _read("AGENTS.md"), _read("docs", "USER_MANUAL.md")
    for a in mod.build_parser()._actions:
        if a.choices and a.option_strings:
            expected = f"`{a.option_strings[-1]} {{{','.join(a.choices)}}}`"     # in the parser's order
            assert expected in agents, f"{module}: {expected} missing from AGENTS.md"
            assert expected in manual, f"{module}: {expected} missing from docs/USER_MANUAL.md"


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
