# Contributing to memristec-skill

Thank you for considering a contribution. This file says how to report a problem, how to
propose a change, and the rules a change has to meet to be merged. The machine-oriented
description of the repository is `AGENTS.md`; the human manual is `docs/USER_MANUAL.md`;
the design decisions and their trade-offs are in `docs/DESIGN.md`.

## Reporting

Open an issue in this repository. The most useful reports carry: what you ran (the exact
command or notebook cell), what you expected, what happened (the full traceback or the
figure), your platform and versions (`python scripts/verify_memristec.py --version`), and,
for anything physical, the reference you checked against. Every physics claim in the
chapters is asserted inline; a claim you can show to be wrong, with the paper, is the most
valuable report. A discrepancy between a model here and the MemrisTec Model Library is
reported with the cross-check numbers (`scripts/upstream_adapter.py` on your own clone).

## Proposing a change

1. Open an issue first for anything larger than a typo, so the scope is agreed before the
   work is done.
2. Fork, branch, and keep the change to one topic.
3. **Failing-first test.** Every bug fix starts with a test that fails on the current code
   and passes on the fix; every feature comes with its tests. `pyflakes` must be clean over
   the whole tree.
4. **Models come from papers, never from the library.** A new model is transcribed from its
   published equation set, cited in `references/models.md` with its default parameters and
   their origin, and cross-checked in numbers through the adapter if the library has a
   folder for it. No line of the MemrisTec Model Library (which has no licence file) may
   enter this repository.
5. Run the suite locally before opening the pull request:

   ```
   python -m pyflakes scripts tests build
   python -m pytest tests -q
   # the notebooks are generated: edit build/part*.py, then
   python build/assemble.py && python build/execute.py --which <chapter-key>
   ```

6. Keep the documentation in step: `README.md`, `SKILL.md`, `AGENTS.md`,
   `docs/USER_MANUAL.md` and `CHANGELOG.md` describe the same repository, and the suite
   fails when a CLI option or a model name drifts from the code.
7. Every new source file carries the SPDX header (`# SPDX-License-Identifier: Apache-2.0`).
8. Do not bump `VERSION`, `CITATION.cff` or tag a release in a pull request; the
   maintainer does that on merge.

## Contributions made with AI assistance

Welcome, on two conditions: say so in the pull request (which tool, what it did), and state
what *you* verified: the test you ran, the derivation you checked, the figure you looked
at. This repository was itself built with an AI assistant under a check-everything
contract (`docs/DESIGN.md`); the same standard applies to contributions.

## Licensing

By submitting a contribution you agree that it is licensed under the repository's licence
(Apache License 2.0), as section 5 of that licence provides for intentional submissions. Do
not contribute code or text you do not have the right to license that way, and do not add
third-party material (upstream sources, downloaded literature, measured data you may not
publish) to the tracked tree.

## Conduct

Everyone interacting in this repository is expected to follow `CODE_OF_CONDUCT.md`.
