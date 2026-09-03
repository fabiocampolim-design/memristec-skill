# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Assemble the chapter notebooks from the part modules in this directory.

The book *MemrisTec Compact Models — Memristor Physics from Paper to Code* is
one notebook per chapter under ``chapters/`` (rule 25: no notebook over 1 MB).
Every chapter runs on its own: a generated header (title, table of contents
with anchors, previous/index/next links), the shared setup cell
(``part00_intro.SETUP_TEMPLATE`` with the figure counter offset so figure
numbers run through the book), the part module's cells, and a generated tally
cell. Section numbers (§1–26) are global. ``chapters/README.md`` (the index)
is generated here too. Cell *outputs* are produced by ``build/execute.py``.

Usage (from memristec-skill/):
    python build/assemble.py                  # every chapter + the index, into chapters/
    python build/assemble.py --which 03       # one chapter (keys from --list)
    python build/assemble.py --outdir out/ -v # elsewhere (a chapters/ folder is created)
    python build/assemble.py --list           # chapters, parts and cell counts; writes nothing

Every invocation appends an audit record to ``<log-dir>/assemble.log``
(default ``<outdir>/logs``).
"""

import argparse
import functools
import importlib
import os
import re
import sys
from collections import namedtuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from nbbuild import write_notebook, md, code  # noqa: E402
from buildlog import AuditLog  # noqa: E402

CHAPTERS_DIR = "chapters"
BOOK_TITLE = "MemrisTec Compact Models — Memristor Physics from Paper to Code"
SECTION_SPAN = "§1–26"

Chapter = namedtuple("Chapter", "key file title parts")
CHAPTERS = [
    Chapter("00", "Memristec_00_Introduction.ipynb", "Introduction", ["part00_intro"]),
    Chapter("01", "Memristec_01_State_Controlled_Resistor.ipynb",
            "The memristor as a state-controlled resistor", ["part01_chua"]),
    Chapter("02", "Memristec_02_Linear_Ion_Drift_and_Windows.ipynb",
            "Linear ion drift and window functions", ["part02_windows"]),
    Chapter("03", "Memristec_03_Threshold_Switching_VTEAM.ipynb",
            "Threshold switching: VTEAM", ["part03_vteam"]),
    Chapter("04", "Memristec_04_Filamentary_Switching.ipynb",
            "Filamentary switching: Stanford–PKU and Yakopcic", ["part04_filament"]),
    Chapter("05", "Memristec_05_Pulses_and_Neuromorphic_Use.ipynb",
            "Pulses, retention and neuromorphic use", ["part05_pulses"]),
    Chapter("06", "Memristec_06_Benchmarking_and_the_Library.ipynb",
            "Benchmarking, numerics, fitting and the MemrisTec library", ["part06_benchmark"]),
]
BY_KEY = {c.key: c for c in CHAPTERS}
MAIN_KEYS = [c.key for c in CHAPTERS]


def present():
    """The chapters whose part modules exist (the book is built one chapter at a time)."""
    return [c for c in CHAPTERS if all(importlib.util.find_spec(p) is not None for p in c.parts)]

SECTION = re.compile(r"^##\s+(\d+)\.\s+(.*)$")               # ## 14. Title
CAPTION_CALL = re.compile(r"(?<!def )(?<![\w.])caption\(")


@functools.lru_cache(maxsize=None)
def _part_cells(name):
    return tuple(importlib.import_module(name).CELLS)


def collect(parts):
    """Return (cells, [(part_name, n_cells), ...]) for the given part modules."""
    cells, per_part = [], []
    for name in parts:
        part = _part_cells(name)
        per_part.append((name, len(part)))
        cells.extend(part)
    return cells, per_part


def headings(cells):
    """[(anchor, label)] for every ``## N. Title`` heading among the cells."""
    out = []
    for kind, src in cells:
        if kind != "md":
            continue
        for line in src.splitlines():
            m = SECTION.match(line.strip())
            if m:
                out.append((f"sec-{int(m.group(1))}", f"§{m.group(1)} {m.group(2).strip()}"))
    return out


def anchored(cells):
    """The same cells with an HTML anchor in front of every heading cell."""
    out = []
    for kind, src in cells:
        if kind == "md":
            for line in src.splitlines():
                m = SECTION.match(line.strip())
                if m:
                    src = f'<a id="sec-{int(m.group(1))}"></a>\n\n' + src.strip("\n")
                    break
        out.append((kind, src))
    return out


def figures_in(cells):
    """Number of figures the cells produce: one ``caption(...)`` call each."""
    return sum(len(CAPTION_CALL.findall(src)) for kind, src in cells if kind == "code")


@functools.lru_cache(maxsize=None)
def figure_offset(key):
    n = 0
    for other in present():
        if other.key == key:
            break
        n += figures_in(collect(other.parts)[0])
    return n


def _label(ch):
    return f"{int(ch.key)} {ch.title}"


def header_cell(key):
    """Generated first cell: title, position in the book, TOC, navigation."""
    ch = BY_KEY[key]
    i = CHAPTERS.index(ch)
    prev_ch = CHAPTERS[i - 1] if i > 0 else None
    next_ch = CHAPTERS[i + 1] if i + 1 < len(CHAPTERS) else None
    cells = collect(ch.parts)[0]
    lines = ['<a id="top"></a>', f"# Chapter {int(ch.key)} — {ch.title}", "",
             f"**{BOOK_TITLE}** · chapter {int(ch.key)} of {len(CHAPTERS) - 1}", ""]
    nav = []
    if prev_ch:
        nav.append(f"[◀ {_label(prev_ch)}]({prev_ch.file})")
    nav.append("[Contents of the book](README.md)")
    if next_ch:
        nav.append(f"[{_label(next_ch)} ▶]({next_ch.file})")
    lines += [" · ".join(nav), ""]
    toc = headings(cells)
    if toc:
        lines += ["**In this chapter**", ""] + [f"- [{label}](#{anchor})" for anchor, label in toc] + [""]
    lines.append("All chapters: " + " · ".join(f"[{int(c.key)}]({c.file})" for c in CHAPTERS))
    lines += ["", "*Every notebook runs on its own: the setup cell below is identical in all of them. "
              f"Section numbers ({SECTION_SPAN}), figure numbers and cross-references are global to the book.*"]
    return md("\n".join(lines))


def tally_cell(key):
    label = f"chapter {int(key)}"
    return code(f'''
# ---- tally for this notebook ---------------------------------------------------
print("=" * 66)
print(f"{label} — checks passed : {{_CHECKS['pass']}}")
print(f"{label} — checks failed : {{_CHECKS['fail']}}")
print(f"wall time{' ' * (len(label) + 8)}: {{time.time() - t_chapter_start:.0f}} s")
print("=" * 66)
print("Every quantitative claim in this notebook was verified in this run."
      if _CHECKS["fail"] == 0 else "Some checks FAILED — search this notebook for '[FAIL]'.")
''')


def chapter_list_markdown():
    lines = []
    for c in present()[1:]:
        secs = [lbl for a, lbl in headings(collect(c.parts)[0])]
        span = f" ({secs[0].split()[0]}–{secs[-1].split()[0]})" if len(secs) > 1 else ""
        lines.append(f"- **[{int(c.key)}. {c.title}]({c.file})**{span}")
    return "\n".join(lines)


def chapter_cells(key):
    """The complete cell list of one chapter notebook — the single source of truth."""
    ch = BY_KEY[key]
    cells = collect(ch.parts)[0]
    import part00_intro as intro
    setup = intro.setup_cell(f"chapter {int(key)}", figure_offset(key))
    if key == "00":
        body = [(k, s.replace("__CHAPTER_LIST__", chapter_list_markdown())) for k, s in cells]
        return body + [setup]
    return [header_cell(key), setup] + anchored(cells) + [tally_cell(key)]


def index_markdown():
    rows = []
    for c in present():
        cells = collect(c.parts)[0]
        secs = [lbl for a, lbl in headings(cells)]
        n_code = sum(1 for k, _ in chapter_cells(c.key) if k == "code")
        if c.key == "00":
            span, name = "", "0 — Introduction"
            what = "what the book is, how to run it, conventions, the shared setup cell"
        else:
            span = f"§{secs[0].split()[0][1:]}–{secs[-1].split()[0][1:]}" if len(secs) > 1 else ""
            name = f"{int(c.key)} — {c.title}"
            what = "; ".join(s.split(" ", 1)[1] for s in secs)
        rows.append(f"| [{name}]({c.file}) | {span} | {n_code} | {what} |")
    return f"""# {BOOK_TITLE}

One notebook per chapter. Each runs on its own (the setup cell is the same in all of them);
section numbers {SECTION_SPAN}, figure numbers and cross-references are global to the book, so "§14"
means section 14 wherever it lives. Start with chapter 0, or jump to any chapter — the header
of each links to the previous and next one and lists its sections. Exercises with worked
solutions close every chapter.

| Notebook | Sections | Code cells | Contents |
|---|---|---|---|
{chr(10).join(rows)}

Generated by `build/assemble.py` from `build/*.py` — do not edit the notebooks or this file by
hand (a test compares them with the sources). Re-execute with `build/execute.py`.
"""


def outputs(root=ROOT):
    return {c.key: os.path.join(root, CHAPTERS_DIR, c.file) for c in CHAPTERS}


def select(which):
    if which in ("all", "main"):
        return [c.key for c in present()]
    if which in BY_KEY:
        return [which]
    raise SystemExit(f"unknown --which {which!r}; use all, main or one of " + ", ".join(BY_KEY))


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--which", default="all", help="all (default), main, or one chapter key (see --list)")
    ap.add_argument("--outdir", default=ROOT, help="repository root receiving chapters/*.ipynb (default: this repository)")
    ap.add_argument("--log-dir", default=None, help="where the audit log goes (default: <outdir>/logs)")
    ap.add_argument("--list", action="store_true", help="print chapters, parts and cell counts, write nothing")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("-v", "--verbose", action="store_true")
    g.add_argument("-q", "--quiet", action="store_true")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    log = AuditLog("assemble", args.outdir, args.log_dir, verbose=args.verbose, quiet=args.quiet, dry=args.list)
    rc = 0
    try:
        keys = select(args.which)
        chapters_dir = os.path.join(args.outdir, CHAPTERS_DIR)
        for key in keys:
            ch = BY_KEY[key]
            cells = chapter_cells(key)
            for name, n in collect(ch.parts)[1]:
                log.debug(f"  {name:<24s} {n:4d} cells")
            if args.list:
                log.info(f"{key:>3s}  {ch.file}: {len(cells)} cells, {figures_in(cells)} figures "
                         f"(numbered from {figure_offset(key) + 1})")
                continue
            os.makedirs(chapters_dir, exist_ok=True)
            out = os.path.join(chapters_dir, ch.file)
            write_notebook(cells, out, echo=False)
            log.info(f"wrote {out} ({len(cells)} cells)")
        if not args.list:
            index = os.path.join(chapters_dir, "README.md")
            with open(index, "w", encoding="utf-8", newline="\n") as f:
                f.write(index_markdown())
            log.info(f"wrote {index}")
    except SystemExit as exc:
        log.error(str(exc))
        rc = 2
    except Exception as exc:  # noqa: BLE001 - the audit log must record any failure
        log.error(f"FAILED: {exc!r}")
        rc = 1
    log.close(rc)
    return rc


if __name__ == "__main__":
    sys.exit(main())
