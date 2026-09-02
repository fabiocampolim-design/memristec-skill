#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Fabio Campolim
# Create the conda env `memristec` and register its Jupyter kernel (Linux/macOS).
# Usage: install_memristec.sh [--dry-run] [--conda /path/to/conda]
DRY=0; CONDA="${CONDA:-conda}"
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY=1;; --conda) CONDA="$2"; shift;; *) echo "unknown arg $1"; exit 2;; esac; shift; done
HERE="$(cd "$(dirname "$0")" && pwd)"; YML="$HERE/../environment-memristec.yml"
status=()
step() { echo "== $1"; echo "   $2"; if [ $DRY = 1 ]; then status+=("$1 : DRY-RUN"); return; fi
         if bash -c "$2"; then status+=("$1 : OK"); else status+=("$1 : FAIL"); printf '%s\n' "${status[@]}"; exit 1; fi; }
command -v "$CONDA" >/dev/null 2>&1 || { echo "FAIL: conda not found ($CONDA)"; exit 1; }
[ -f "$YML" ] || { echo "FAIL: $YML missing"; exit 1; }
step create-env      "$CONDA env create -f '$YML' -y"
step register-kernel "$CONDA run -n memristec python -m ipykernel install --user --name memristec-mc --display-name 'Python 3.12 (memristec)'"
step verify-imports  "$CONDA run -n memristec python -c 'import numpy, scipy, matplotlib, yaml, pytest; print(\"imports ok\")'"
printf '%s\n' "${status[@]}"
