# memristec-skill

An AI-agent skill, a verified Python toolkit, six executed chapter notebooks
and (next) an undergraduate course on **compact memristor models**, built by
studying the [MemrisTec Memristor Model Platform](https://memristec.de/memristor-model-platform/)
end to end. Version 0.2.0 ships four model families written from their
papers — linear ion drift (no / Joglekar / Biolek / Prodromakis windows),
Yakopcic 2013, VTEAM 2015 and the Stanford–PKU filamentary model (Jiang 2016)
— on one ODE driver, with I-V sweeps, pinched-loop metrics, dynamic route
maps, pulse programming, and an optional cross-check against a local clone of
the MemrisTec Model Library (agreement 2e-16 … 4e-15 in the derivative fields).

## Quick start

```bash
scripts/install_memristec_windows.ps1        # or scripts/install_memristec.sh
python scripts/verify_memristec.py           # exit 0 = environment and physics OK
python scripts/memristec_tools.py --selftest
python -m pytest tests -q
```

Manual: `docs/USER_MANUAL.md`. For AI agents: `SKILL.md`, `AGENTS.md`.
Design notes: `docs/DESIGN.md`. Contributing: `CONTRIBUTING.md`.

## The book

Six executed chapter notebooks under `chapters/` re-derive the model families of the
MemrisTec Model Library from their papers and run them through one driver: the memristor as
a state-controlled resistor (Chua, Strukov's affine law, the pinched loop), linear ion drift
and its window functions, threshold switching with VTEAM, filamentary switching with the
Stanford–PKU and Yakopcic models, pulse programming and neuromorphic hand-off, and
benchmarking, numerics, fitting and the cross-check against the library. Every figure is
generated live and every claim is checked — 83 inline checks, 25 figures, 0 failures
(`chapters/README.md`). The notebooks are generated from `build/*.py` — do not edit them by
hand.

## Licence

Apache License 2.0 — see `LICENSE` and `NOTICE`. The MemrisTec Model Library
itself is studied, not redistributed; every model here is written from its
published paper (`references/models.md`).

### Disclaimer

This software is provided "as is", without warranty of any kind, express or
implied, including but not limited to the warranties of merchantability,
fitness for a particular purpose and non-infringement. In no event shall the
authors be liable for any claim, damages or other liability arising from,
out of or in connection with the software or its use. This project is
independent and not affiliated with or endorsed by MemrisTec, the DFG,
TU Dresden or RWTH Aachen University.
