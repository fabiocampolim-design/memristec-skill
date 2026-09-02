# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Withheld-material guard.

Part of the owner's ongoing, unpublished research was removed from this
repository on 2026-08-29 and must not come back into any tracked file — text,
code, notebook outputs or docs — until it is published. The forbidden tokens
are stored as SHA-256 hashes in ``tests/held_terms.txt`` so that neither this
file nor that list names the topic. See ``held/README.md`` (local only) for
what was removed and how to restore it later.
"""

import hashlib
import os
import re
import subprocess

import pytest

from conftest import ROOT

TEXT_EXT = {".py", ".md", ".ipynb", ".txt", ".yml", ".yaml", ".json", ".ps1", ".bib", ".cff"}
TERMS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "held_terms.txt")
TOKEN = re.compile(r"[^\W\d_](?:[\w\-]*[^\W\d_])?", re.UNICODE)   # words, incl. hyphenated


def held_hashes():
    with open(TERMS_FILE, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}


def tracked_text_files():
    """Every tracked text file of the *whole* git repository (this product may
    live inside a larger study repository — scan all of it)."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
        out = subprocess.run(["git", "ls-files"], cwd=top, capture_output=True,
                             text=True, check=True).stdout
        return [os.path.join(top, p) for p in out.split() if os.path.splitext(p)[1] in TEXT_EXT]
    except Exception:  # noqa: BLE001 - no git: fall back to the shipped scripts
        scripts = os.path.join(ROOT, "scripts")
        return sorted(os.path.join(scripts, p) for p in os.listdir(scripts)
                      if os.path.splitext(p)[1] in TEXT_EXT)


def offending_tokens(line, hashes):
    for tok in TOKEN.findall(line):
        low = tok.lower()
        for cand in (low, low.strip("-"), low.replace("-", "")):
            if hashlib.sha256(cand.encode("utf-8")).hexdigest() in hashes:
                return tok
    return None


@pytest.mark.parametrize("path", tracked_text_files(), ids=lambda p: os.path.basename(p))
def test_no_held_tokens_in_tracked_file(path):
    if not os.path.exists(path):
        pytest.skip("deleted in working tree")
    hashes = held_hashes()
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            tok = offending_tokens(line, hashes)
            assert tok is None, f"{os.path.relpath(path, ROOT)}:{i}: {tok!r} — withheld material"


def test_guard_mechanism_fires_on_a_listed_token():
    # self-check of the mechanism with a dummy word (the real list is not inverted here)
    dummy = "zzqx-dummyword"
    hashes = {hashlib.sha256(dummy.encode()).hexdigest()}
    assert offending_tokens(f"text with {dummy.upper()} inside", hashes) == dummy.upper()
    assert offending_tokens("clean line", hashes) is None
    real = held_hashes()
    assert real and all(re.fullmatch(r"[0-9a-f]{64}", h) for h in real)


def test_held_directory_is_ignored():
    """The study repository that contains this product must ignore `held/`;
    when the product is published on its own there is no held/ at all."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        pytest.skip("not inside a git repository")
    if not os.path.isdir(os.path.join(top, "held")):
        pytest.skip("no held/ directory in this checkout")
    with open(os.path.join(top, ".gitignore"), encoding="utf-8") as f:
        assert "held/" in f.read()
