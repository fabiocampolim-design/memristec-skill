# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Playbook rule 17: the warranty disclaimer and limitation of liability must
survive every rewrite — in LICENSE, visibly in the README, and every source
file must carry the SPDX header."""

import glob
import os

from conftest import ROOT


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8", errors="replace") as f:
        return f.read()


def test_license_is_apache_2_with_disclaimers():
    text = _read("LICENSE")
    assert "Apache License" in text and "Version 2.0" in text
    assert "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND" in text
    assert "Limitation of Liability" in text


def test_notice_names_project_and_upstream_status():
    text = _read("NOTICE")
    assert "memristec-skill" in text and "Apache License, Version 2.0" in text
    assert "contains no code from that library" in text
    assert "not affiliated" in text


def test_readme_carries_visible_disclaimer_under_licence():
    text = _read("README.md")
    assert "## Licence" in text and "### Disclaimer" in text
    assert text.index("## Licence") < text.index("### Disclaimer")
    low = text.lower()
    assert "without warrant" in low and "liable" in low and "not affiliated" in low


def test_skill_frontmatter_and_citation_match_licence():
    assert "license: Apache-2.0" in _read("SKILL.md")
    assert "license: Apache-2.0" in _read("CITATION.cff")


def test_every_python_file_has_spdx_header():
    files = [f for pat in ("scripts/*.py", "tests/*.py", "docs/*.py")
             for f in glob.glob(os.path.join(ROOT, pat))]
    assert files
    missing = [f for f in files if "SPDX-License-Identifier: Apache-2.0" not in _read(f)[:300]]
    assert not missing, [os.path.relpath(m, ROOT) for m in missing]
