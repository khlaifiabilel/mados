# Contributing to neuralq-s2sr-mados

This repository follows the [NeuralQ Handbook](https://github.com/NeuralQ/neuralq-handbook)
engineering standards. The short version:

## Workflow

- **Trunk-based development.** Branch from `main` as
  `feature/<ticket-id>-<short-description>`; merge back within 3 business days.
  Hotfixes use `hotfix/<ticket-id>-<short-description>` and live at most 1 day.
- **No direct commits to `main`.** Everything goes through a PR with at least
  one review (two for changes to authentication, infrastructure, database
  migrations, or the ML training/serving pipeline — see the handbook
  [Code Review Standards](https://github.com/NeuralQ/neuralq-handbook/blob/main/engineering/code-review.md)).
- **Conventional Commits** for all commit messages and PR titles
  (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`).
- **Squash and merge**; delete the feature branch afterwards.
- Reviewers have a **24-hour SLA** for first feedback.

The fork's default branch and remote are being aligned with org policy
(`main` on the NeuralQ organisation); base new branches on `main`.

## Local setup

Python **3.10** is the target runtime (`environment.yml` pins `python=3.10.21`).

### Full environment (training and evaluation)

```bash
conda create -n neuralq-s2sr-mados python=3.10
conda activate neuralq-s2sr-mados
python -m pip install -r requirements.txt
```

`environment.yml` is the complete conda export of the experiment environment;
use it when you also need the GDAL/PROJ system libraries imported by
`utils/dataset.py` and `utils/spectral_extraction.py`:

```bash
conda env create -f environment.yml
conda activate neuralq-s2sr-mados
```

### Test-only environment (what CI uses)

The CI job installs nothing but the pinned test dependencies, so it stays
fast and runs without a GPU:

```bash
python -m pip install "numpy==2.2.6" "pytest==8.3.5"
```

### Data and weights

| Artifact | Where it goes | Source |
| --- | --- | --- |
| MADOS dataset | `data/MADOS` | [Zenodo DOI 10.5281/zenodo.10664073](https://doi.org/10.5281/zenodo.10664073) |
| 5 pretrained MariNeXt runs | `marinext/trained_models/` (`*.pth`) | Google Drive link in `README.md` |
| `dataset.h5` spectral table | `data/dataset.h5` | Google Drive link in `README.md` |

None of these are committed; `evaluation.py` globs `*.pth` from `--model_path`.

### Repository layout

| Path | Purpose |
| --- | --- |
| `marinext/` | `train.py`, `evaluation.py` and the MariNeXt wrapper |
| `marinext/mmseg/` | vendored mmsegmentation model/ops code used by the wrapper |
| `marinext/configs/` | mmengine model configs, loaded by `marinext_wrapper.py` |
| `utils/` | dataset loading, metrics, `vscp.py`, `stack_patches.py`, `spectral_extraction.py` |
| `utils/test_time_aug.py` | the eight-way rotation/flip test-time augmentation used by evaluation (needs torch, so it is exercised by the evaluation run rather than by CI) |
| `tests/` | dependency-light deterministic unit tests run by CI |
| `data/`, `logs/`, `notebooks/`, `s2sr-data/` | local artifacts only — never committed |

## Quality gates

| Gate | Requirement |
| --- | --- |
| Lint | `git ls-files -z '*.py' \| xargs -0 -r python -m py_compile` passes on every tracked source (the repository ships no ruff/black configuration yet, so byte-compilation is the enforced syntax gate) |
| Tests | `python -m pytest tests/ -q` green; no network, no GPU, no wall-clock dependence |
| Secrets | No credentials, tokens, keys, or client data in the diff |
| Data | No dataset rasters, HDF5 tables, checkpoints, prediction masks, or logs in the diff |
| Docs | README updated for behaviour changes; ADR for significant decisions |

Handbook coverage thresholds (≥ 80% on new code) apply; coverage reporting is
not yet wired into this repository's CI.

## Pull request description

Include: **What**, **Why**, **How**, **Testing**, and the ticket link.
Assign at least one reviewer and apply the appropriate labels.

## Documentation

- Code comments explain **why**, not **what**; no commented-out code.
- Significant architectural decisions are recorded as ADRs in `docs/adrs/`
  using the handbook
  [ADR format](https://github.com/NeuralQ/neuralq-handbook/blob/main/engineering/documentation.md).
- Operational guides and runbooks live in `docs/runbooks/`.
- Public entry points need Google-style docstrings.

## Data and security

- Never commit secrets, credentials, imagery, tensors, or client data.
  Configuration values are read from environment variables or a secrets
  manager (see the handbook
  [Security & Data Policy](https://github.com/NeuralQ/neuralq-handbook/blob/main/policies/security-and-data.md)).
- The MADOS dataset and the pretrained checkpoints stay external links; they
  are never vendored into Git.
- Report vulnerabilities privately through the process in
  [`SECURITY.md`](SECURITY.md) — never in a public issue.
- Test data must be synthetic, anonymized, or drawn from approved sample
  datasets, with fixed seeds for determinism.

## Handbook

Something in the standards wrong or outdated? Propose a change via the
[handbook contribution process](https://github.com/NeuralQ/neuralq-handbook/blob/main/CONTRIBUTING.md)
and note it in the handbook `CHANGELOG.md`.
