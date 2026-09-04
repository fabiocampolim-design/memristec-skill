# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""The real regression suite: the notebooks themselves.

Fast part (always runs): every committed chapter notebook is fully executed
with 0 FAIL / 0 error outputs, matches what build/assemble.py generates from
build/*.py, carries the generated header (title, TOC, navigation) and is
small enough to open (rule 25). Book-wide minimum counts guard against silent
loss. Slow part (``--run-notebooks``): re-execute every chapter on the pinned
kernel into a temporary directory and tally again (skips without the kernel).
"""

import json
import os
import re
import subprocess
import sys

import pytest

from conftest import ROOT

sys.path.insert(0, os.path.join(ROOT, "build"))
from assemble import BY_KEY, CHAPTERS, chapter_cells, headings, collect, index_markdown, outputs  # noqa: E402
from execute import tally, tally_series  # noqa: E402
from nbbuild import make_cell  # noqa: E402

KEYS = [c.key for c in CHAPTERS]
PATHS = outputs(ROOT)
COMMITTED = [k for k in KEYS if os.path.exists(PATHS[k])]     # chapters land one task at a time
EXPECTED = {"cells": 68, "pass": 70, "figures": 21}           # raised by every chapter task
MAX_NOTEBOOK_BYTES = 1_500_000
TARGET_NOTEBOOK_BYTES = 1_000_000


def _nb(key):
    with open(PATHS[key], encoding="utf-8") as f:
        return json.load(f)


def kernel_available(name="memristec-mc"):
    try:
        out = subprocess.run([sys.executable, "-m", "jupyter", "kernelspec", "list"],
                             capture_output=True, text=True, timeout=60)
        return name in out.stdout
    except Exception:  # noqa: BLE001
        return False


def test_every_planned_chapter_is_committed_once_the_book_is_complete():
    missing = [k for k in KEYS if k not in COMMITTED]
    assert not missing or os.environ.get("MEMRISTEC_BOOK_IN_PROGRESS"), f"missing chapters {missing}"


@pytest.mark.parametrize("key", COMMITTED)
def test_committed_notebook_is_green(key):
    t = tally(PATHS[key])
    assert t["fail"] == 0, t["fail_labels"]
    assert t["errors"] == 0
    assert t["unexecuted"] == 0
    assert t["captions"] == t["figures"], "every figure must carry a caption"
    if key != "00":
        assert t["pass"] >= 1, "a chapter without any check is not verified"


def test_book_totals_do_not_regress():
    t = tally_series([PATHS[k] for k in COMMITTED])
    for k, v in EXPECTED.items():
        assert t[k] >= v, (k, t[k], v)


@pytest.mark.parametrize("key", COMMITTED)
def test_committed_notebook_matches_builder_sources(key):
    built = ["".join(make_cell(k, s)["source"]) for k, s in chapter_cells(key)]
    nb = _nb(key)
    stored = ["".join(c["source"]) for c in nb["cells"]]
    assert len(built) == len(stored), f"{key}: {len(built)} cells built, {len(stored)} stored"
    for i, (a, b) in enumerate(zip(built, stored)):
        assert a.strip() == b.strip(), f"{key}: cell {i} differs from build/ sources"
    assert nb["metadata"]["kernelspec"]["name"] == "memristec-mc"


def test_index_matches_builder_sources():
    with open(os.path.join(ROOT, "chapters", "README.md"), encoding="utf-8") as f:
        assert f.read() == index_markdown(), "run build/assemble.py (chapters/README.md is generated)"


@pytest.mark.parametrize("key", COMMITTED)
def test_notebook_is_small_enough_to_open(key):
    size = os.path.getsize(PATHS[key])
    assert size <= MAX_NOTEBOOK_BYTES, f"{BY_KEY[key].file} is {size / 1e6:.2f} MB — split it"
    assert size <= TARGET_NOTEBOOK_BYTES, f"{BY_KEY[key].file} is {size / 1e6:.2f} MB — over the 1 MB target (rule 25)"


@pytest.mark.parametrize("key", [k for k in COMMITTED if k != "00"])
def test_chapter_header_has_toc_and_navigation(key):
    ch = BY_KEY[key]
    cells = _nb(key)["cells"]
    head = "".join(cells[0]["source"])
    assert cells[0]["cell_type"] == "markdown"
    assert head.startswith('<a id="top"></a>\n# ')
    assert "[Contents of the book](README.md)" in head
    anchors = {a for a, _ in headings(collect(ch.parts)[0])}
    assert anchors, "a chapter must have at least one section heading"
    for anchor in anchors:
        assert f"](#{anchor})" in head, f"{key}: TOC entry for #{anchor} missing"
    body = "".join("".join(c["source"]) for c in cells[1:])
    for anchor in anchors:
        assert f'<a id="{anchor}"></a>' in body, f"{key}: anchor #{anchor} missing"
    i = CHAPTERS.index(ch)
    if i > 0:
        assert f"]({CHAPTERS[i - 1].file})" in head, "previous-chapter link missing"
    if i + 1 < len(CHAPTERS):
        assert f"]({CHAPTERS[i + 1].file})" in head, "next-chapter link missing"


@pytest.mark.parametrize("key", [k for k in COMMITTED if k != "00"])
def test_every_chapter_runs_on_its_own(key):
    cells = _nb(key)["cells"]
    codes = [c for c in cells if c["cell_type"] == "code"]
    assert "shared setup" in "".join(codes[0]["source"])
    assert "tally for this notebook" in "".join(cells[-1]["source"])
    text = "".join(o.get("text", "") if isinstance(o.get("text"), str) else "".join(o.get("text", []))
                   for o in cells[-1].get("outputs", []))
    assert "checks failed : 0" in text


def test_figure_numbers_run_through_the_book():
    expected = 1
    for key in COMMITTED:
        for c in _nb(key)["cells"]:
            for o in c.get("outputs", []) if c["cell_type"] == "code" else []:
                html = "".join(o.get("data", {}).get("text/html", []))
                m = re.search(r"<b>Figure (\d+)\.</b>", html)
                if m:
                    assert int(m.group(1)) == expected, (key, m.group(1), expected)
                    expected += 1


@pytest.mark.parametrize("key", COMMITTED)
def test_no_personal_paths_or_codenames_in_notebook(key):
    with open(PATHS[key], encoding="utf-8") as f:
        blob = f.read()
    win_home = "C:" + "\\\\" + "Users" + "\\\\"          # JSON-escaped form found in .ipynb
    posix_home = "/c/" + "Users/"
    mail = "@" + "gm" + "ail"
    for needle in (win_home, posix_home, mail):
        assert needle not in blob, f"{key}: {needle!r} leaked into the notebook"


@pytest.mark.skipif(not kernel_available(), reason="kernel memristec-mc not registered")
@pytest.mark.parametrize("key", COMMITTED)
def test_reexecuted_notebook_is_green(key, tmp_path, request):
    if not request.config.getoption("--run-notebooks", default=False):
        pytest.skip("pass --run-notebooks to re-execute the chapters")
    from execute import main as execute_main
    rc = execute_main(["--which", key, "--outdir", str(tmp_path), "-q"])
    assert rc == 0
    t = tally(os.path.join(tmp_path, "chapters", BY_KEY[key].file))
    assert t["fail"] == 0 and t["errors"] == 0
