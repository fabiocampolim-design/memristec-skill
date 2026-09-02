# memristec-skill

An AI-agent skill, a verified Python toolkit and (later) executed chapter
notebooks and an undergraduate course on **compact memristor models**, built
by studying the [MemrisTec Memristor Model Platform](https://memristec.de/memristor-model-platform/)
end to end. Version 0.1.0 is the foundation: the linear-ion-drift family
(no / Joglekar / Biolek / Prodromakis windows), the Yakopcic 2013 model, a
shared ODE driver, I-V sweeps, pinched-loop metrics, a dynamic route map, and
an optional cross-check against a local clone of the MemrisTec Model Library.

## Quick start

```bash
scripts/install_memristec_windows.ps1        # or scripts/install_memristec.sh
python scripts/verify_memristec.py           # exit 0 = environment and physics OK
python scripts/memristec_tools.py --selftest
python -m pytest tests -q
```

Manual: `docs/USER_MANUAL.md`. For AI agents: `SKILL.md`, `AGENTS.md`.

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
