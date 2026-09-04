# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Draw the device-class / public-data / model-family map as a static SVG for the README.

The interactive version lives in the study repository's data atlas; this one is the
same three columns with fixed colours that read on GitHub's light and dark grounds.

Usage:
    python build/map_figure.py                # writes docs/figures/memristor-map.svg
    python build/map_figure.py --out PATH
"""

import argparse
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
DEFAULT_OUT = os.path.join(ROOT, "docs", "figures", "memristor-map.svg")

CLASSES = [
    ("vcm", "VCM oxide", "TiOx · HfOx · TaOx · SiOx"),
    ("ecm", "ECM / CBRAM", "Ag, Cu filaments · Ag2S · SDC"),
    ("pcm", "Phase change", "GeSbTe"),
    ("thr", "Threshold / OTS", "volatile, NDR"),
    ("org", "Organic / molecular", "polymers · single molecules"),
    ("per", "Perovskite / other ionic", "halide perovskite · MOF · iontronic"),
]
MODELS = [
    ("lid", "Linear ion drift + window", "linear_ion_drift"),
    ("yak", "Yakopcic 2013", "yakopcic2013"),
    ("vte", "VTEAM 2015", "vteam2015"),
    ("phy", "Stanford–PKU · JART", "stanford_pku2016"),
    ("the", "Thermal threshold", "adapter only"),
    ("dd", "Data-driven", "adapter only"),
]
# (label, classes, model families) — the public data sets of references/taxonomy.md
DATA = [
    ("Southampton TiO2 data-driven ReRAM data", ["vcm"], ["dd", "yak", "vte"]),
    ("Fabrication-to-modeling database (6 190 devices)", ["vcm"], ["phy", "yak", "vte", "dd"]),
    ("Southampton benchmarking methodology set", ["vcm"], ["yak", "vte", "phy"]),
    ("Southampton variability / secure ID", ["vcm"], ["dd"]),
    ("Southampton threshold-logic gates", ["vcm"], ["vte"]),
    ("Southampton SiC memristor sets", ["vcm"], ["yak", "vte"]),
    ("UCL SiO2 edge-detection set", ["vcm"], ["yak", "dd"]),
    ("TiO2 resistive drift (IEEE DataPort)", ["vcm"], ["dd"]),
    ("RSCT benchmark (8 sets, 7 families)", ["ecm", "vcm", "org", "per"], ["yak", "vte", "dd"]),
    ("Knowm SDC memristors", ["ecm"], ["yak", "vte"]),
    ("Prussian-blue MOF C-AFM data", ["per"], ["yak"]),
    ("Carbazole polymer PPF / STDP", ["org"], ["yak"]),
    ("Single-molecule switches (Delft)", ["org"], []),
    ("Perovskite I-V data paper", ["per"], ["yak", "dd"]),
    ("Southampton UV-assisted hybrid cells", ["org", "vcm"], ["yak"]),
    ("Southampton 1S1R OTS selector + memory", ["thr", "vcm"], ["the", "vte"]),
    ("Southampton GeSbTe phase-change sets", ["pcm"], []),
    ("IBM aihwkit PCM statistical model", ["pcm"], ["dd"]),
    ("MemrisTec model table (model outputs)", ["vcm", "thr"], ["lid", "yak", "vte", "phy", "the", "dd"]),
]

# Fixed colours chosen to read on white and on GitHub's dark ground.
INK, MUTED, EDGE = "#3B4753", "#6B7A88", "#A9B6C2"
TEAL, TEAL_BG = "#0C7C84", "#D5EBEC"
AMBER, AMBER_BG = "#B8690F", "#F6E4CC"
VIOLET, VIOLET_BG = "#5B4A9E", "#E3DEF2"
FONT = "'IBM Plex Sans', 'Segoe UI', Helvetica, Arial, sans-serif"


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(width=1180, height=720):
    top, bottom = 56, height - 16
    col = {"c": (20, 290), "d": (430, 380), "m": (960, 200)}

    def ys(n):
        step = (bottom - top) / n
        return [top + step * i + step / 2 for i in range(n)]

    yc, yd, ym = ys(len(CLASSES)), ys(len(DATA)), ys(len(MODELS))
    pos = {}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
           f'font-family="{FONT}" role="img" aria-label="Memristor device classes, public data sets and the '
           f'compact-model families that fit them">',
           '<rect width="100%" height="100%" fill="#FFFFFF" rx="8"/>']
    for x, label in ((20, "DEVICE CLASS"), (430, "PUBLIC DATA SET"), (960, "MODEL FAMILY")):
        out.append(f'<text x="{x}" y="30" font-size="13" font-weight="700" letter-spacing="1.2" fill="{MUTED}">{label}</text>')
    edges = []
    for (cid, _, _), y in zip(CLASSES, yc):
        pos[cid] = (col["c"][0], y, col["c"][1])
    for i, (label, _, _) in enumerate(DATA):
        pos[f"d{i}"] = (col["d"][0], yd[i], col["d"][1])
    for (mid, _, _), y in zip(MODELS, ym):
        pos[mid] = (col["m"][0], y, col["m"][1])

    def edge(a, b, color):
        x1 = pos[a][0] + pos[a][2]
        y1 = pos[a][1]
        x2, y2 = pos[b][0], pos[b][1]
        dx = (x2 - x1) * 0.5
        edges.append(f'<path d="M{x1:.0f},{y1:.1f} C{x1 + dx:.0f},{y1:.1f} {x2 - dx:.0f},{y2:.1f} {x2:.0f},{y2:.1f}" '
                     f'fill="none" stroke="{color}" stroke-width="1.2" opacity="0.8"/>')

    for i, (_, classes, models) in enumerate(DATA):
        for c in classes:
            edge(c, f"d{i}", EDGE)
        for m in models:
            edge(f"d{i}", m, EDGE)
    out.extend(edges)

    def box(x, y, w, h, fill, stroke, title, sub=None, size=13):
        out.append(f'<rect x="{x}" y="{y - h / 2:.1f}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>')
        ty = y - 1 if sub else y + 4.5
        out.append(f'<text x="{x + 10}" y="{ty:.1f}" font-size="{size}" fill="{INK}">{_esc(title)}</text>')
        if sub:
            out.append(f'<text x="{x + 10}" y="{y + 13:.1f}" font-size="10.5" fill="{MUTED}">{_esc(sub)}</text>')

    for (cid, label, sub), y in zip(CLASSES, yc):
        box(col["c"][0], y, col["c"][1], 42, TEAL_BG, TEAL, label, sub)
    for i, (label, _, _) in enumerate(DATA):
        box(col["d"][0], yd[i], col["d"][1], 26, AMBER_BG, AMBER, label, size=12.5)
    for (mid, label, sub), y in zip(MODELS, ym):
        box(col["m"][0], y, col["m"][1], 42, VIOLET_BG, VIOLET, label, sub)
    out.append("</svg>\n")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=DEFAULT_OUT, help="output SVG path (default docs/figures/memristor-map.svg)")
    args = ap.parse_args(argv)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(build())
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
