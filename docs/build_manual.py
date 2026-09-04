# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Build docs/USER_MANUAL.md into HTML and PDF.

Uses pandoc (and a LaTeX engine for the PDF) when they are on PATH and degrades
gracefully: without pandoc a small built-in Markdown-to-HTML converter produces the
HTML and the PDF step is skipped with a notice. The outputs are not tracked; the
Markdown is the source.

Usage:
    python docs/build_manual.py                # docs/USER_MANUAL.{html,pdf}
    python docs/build_manual.py --outdir out/  # elsewhere
    python docs/build_manual.py --no-pdf -v
Exit 0 on success, 1 when pandoc or the PDF engine fails.
"""

import argparse
import html
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "USER_MANUAL.md")
TITLE = "memristec-skill — User Manual"


def _inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html_minimal(text):
    """Markdown subset: headings, paragraphs, lists, fenced code, pipe tables, inline code/bold/links."""
    out, in_code, in_list, in_table = [], False, False, False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
            out.append("<pre><code>" if in_code else "</code></pre>")
            continue
        if in_code:
            out.append(html.escape(line))
            continue
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            tag = "th" if out[-1] == "<table>" else "td"
            out.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + _inline(re.sub(r"^\s*[-*]\s+", "", line)) + "</li>")
            continue
        if in_list and not line.strip():
            out.append("</ul>")
            in_list = False
        if line.strip():
            out.append("<p>" + _inline(line) + "</p>")
    if in_list:
        out.append("</ul>")
    if in_table:
        out.append("</table>")
    return "\n".join(out)


STYLE = ("<style>body{max-width:860px;margin:2em auto;font:15px/1.5 system-ui,sans-serif;padding:0 1em}"
         "code,pre{font-family:ui-monospace,Consolas,monospace;font-size:.92em}pre{background:#f4f4f4;padding:.8em;overflow-x:auto}"
         "table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:.3em .6em;vertical-align:top}th{background:#eee}</style>")


def build_parser():
    ap = argparse.ArgumentParser(prog="build_manual", description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", default=HERE, help="where USER_MANUAL.html / .pdf go (default docs/)")
    ap.add_argument("--no-pdf", action="store_true", help="write the HTML only")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the converter used and the commands")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    os.makedirs(args.outdir, exist_ok=True)
    html_out = os.path.join(args.outdir, "USER_MANUAL.html")
    pdf_out = os.path.join(args.outdir, "USER_MANUAL.pdf")
    pandoc = shutil.which("pandoc")
    try:
        if pandoc:
            cmd = [pandoc, SRC, "-s", "--toc", "-o", html_out, "--metadata", f"title={TITLE}"]
            if args.verbose:
                print(" ".join(cmd))
            subprocess.run(cmd, check=True)
            print(f"wrote {html_out} (pandoc)")
        else:
            with open(SRC, encoding="utf-8") as f:
                body = md_to_html_minimal(f.read())
            with open(html_out, "w", encoding="utf-8") as f:
                f.write(f"<!doctype html><meta charset='utf-8'><title>{html.escape(TITLE)}</title>" + STYLE + body)
            print(f"wrote {html_out} (built-in converter; install pandoc for a nicer build)")
        if args.no_pdf:
            return 0
        engine = next((e for e in ("xelatex", "lualatex") if shutil.which(e)), None)
        if not (pandoc and engine):
            print("PDF skipped: needs pandoc + xelatex/lualatex on PATH")
            return 0
        cmd = [pandoc, SRC, "-o", pdf_out, f"--pdf-engine={engine}", "--toc", "-V", "geometry:margin=2.2cm",
               "-V", "mainfont=DejaVu Serif", "-V", "monofont=DejaVu Sans Mono", "--metadata", f"title={TITLE}"]
        if args.verbose:
            print(" ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"wrote {pdf_out} ({engine})")
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"build_manual: FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
