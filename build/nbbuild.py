# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
"""Tiny notebook builder for the memristec-skill chapter notebooks.

Each part module defines CELLS = [("md", "..."), ("code", "..."), ...].
assemble.py concatenates them and writes the .ipynb (kernel: memristec-mc).
"""

import json

KERNELSPEC = {
    "display_name": "Python 3.12 (memristec)",
    "language": "python",
    "name": "memristec-mc",
}


def md(source):
    return ("md", source)


def code(source):
    return ("code", source)


def make_cell(kind, source):
    src = source.strip("\n")
    if kind == "md":
        return {"cell_type": "markdown", "metadata": {}, "source": src}
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": src}


def write_notebook(cells, path, echo=True):
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": dict(KERNELSPEC),
                     "language_info": {"name": "python", "version": "3.12"}},
        "cells": [make_cell(kind, src) for kind, src in cells],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    if echo:
        print(f"wrote {path}  ({len(cells)} cells)")
