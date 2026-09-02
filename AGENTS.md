# AGENTS.md — memristec-skill for AI agents

Product root: this directory. Run everything from here with the `memristec`
conda env and `PYTHONIOENCODING=utf-8`.

| Task | Command |
|---|---|
| Health check | `python scripts/verify_memristec.py` |
| Toolkit self-test | `python scripts/memristec_tools.py --selftest` |
| Fast suite | `python -m pytest tests -q` |
| Cross-check against a local upstream clone | `MEMRISTEC_MODEL_LIBRARY=<clone> python -m pytest tests/test_upstream_crosscheck.py -q` |

Flags are documented per script below (the suite fails when one is missing).

(Filled in by the foundation plan, Task 7.)
