# The MemrisTec Memristor Model Platform — what it is, how we read it

MemrisTec is the DFG priority programme SPP 2262 "Memristive Devices for
Intelligent Technical Systems" (2020–2026, coordinated at TU Dresden). Its
**Model Platform** has four parts:

| part | URL | what |
|---|---|---|
| overview | https://memristec.de/memristor-model-platform/ | entry page |
| model table | https://memristec.de/memristec-model-table/ | filterable table generated from each model's `model.json` |
| model simulator | https://memristec.de/model-simulation/ | browser front end that runs selected models |
| model repository | https://git-ce.rwth-aachen.de/memristec/memristec-model-library | the Python model library (RWTH Aachen GitLab) |
| circuit simulation | announced as "coming soon" (2026-09) | — |

This skill studies the whole platform and **ships none of it**: models are
re-derived from their papers (`references/models.md`); the repository is
read only through your own clone.

## The model library

- One folder per model under `models/`: `model.py` (a class), `model.json`
  (metadata for the website), optionally `model.yml` (parameters) and one
  or two images (quasi-static I-V, dynamic route map).
- There is **no common interface**: every `model.py` chooses its own class
  and method names, its own parameter source (yml, keyword defaults,
  hard-coded) and mostly builds its own sine stimulus. `upstream_adapter.py`
  wraps the folders it knows (`SHIMS`) behind `state_derivative(x, v)` /
  `current(x, v)` / `x0` / `params`.
- Branches (2026-09): `main` (website names, last commit 2026-05) and
  `dev` (active code line, last commit 2026-07, 83 commits ahead, six
  folders renamed) plus two dormant early branches. No tags, no CI, no
  packaging, **no licence file** — the code is all-rights-reserved by
  default, which is why nothing from it may be redistributed here.

### `model.json` fields (in our words, from the upstream template notes)

| field | meaning / allowed values |
|---|---|
| `name` | folder-style model name, usually `<Group or first author><Year>` |
| `modelType` | `memristive`, `memcapacitive`, `meminductive` |
| `DOI`, `source` | DOI and web link of the paper the model implements |
| `languages[]` | `{language, link}` pairs: other implementations (SPICE, MATLAB, MemTorch, …) |
| `materials[]` | `{material, type}` pairs describing the device stack (`metal` / `insulator`) |
| `category`, `description` | free text shown on the website |
| `volatility` | `Non-volatile` or `Volatile` |
| `switchingType` | `Bipolar Switching` or `Unipolar Switching` |
| `switchingGeometry` | `Filamentary` or `Area-dependent` (may be an array) |
| `physics` | `Valence change memory (VCM)`, `Electrochemical metallization (ECM)`, `Phase change memory (PCM)`, `Thermochemical memory (TCM)`; in practice also `Threshold Switching`, `Ternary Content Addressable Memory`, `Further` |
| `imageIV`, `imageDynamic` | paths of the two plots (quasi-static I-V; dynamic route map or similar) |
| `imagedR-dV`, `imageR-V`, `imageWindowFunction` | optional extra plots |
| `windowFunction` | `biolek`, `prodromakis`, `joglekar` (case varies upstream), `None`, `exponential`, or empty |

## Access notes

- The GitLab **web pages and API sit behind an Anubis proof-of-work
  challenge**: plain HTTP fetches fail; `git clone` / `git fetch` work.
  Issues and merge requests are read in a browser and filed only by a
  human.
- The repository carries more than 1 GB of committed notebook outputs. A
  partial clone keeps it usable:

  ```bash
  git clone --filter=blob:none --no-checkout https://git-ce.rwth-aachen.de/memristec/memristec-model-library
  cd memristec-model-library && git checkout main
  ```

  In such a clone never `git diff` across branches (every blob is a network
  round trip); use `git ls-tree`, `git log`, `git show <ref>:<path>`.

## Pointing this skill at your clone

```bash
export MEMRISTEC_MODEL_LIBRARY=/path/to/memristec-model-library   # the folder containing models/
python scripts/verify_memristec.py            # adds the upstream cross-check line
python scripts/upstream_adapter.py            # compares every shimmed folder, writes an audit log
python -m pytest tests/test_upstream_crosscheck.py -q
```

Without the variable those checks skip; nothing else changes.
