# Security Policy

This repository is a NeuralQ-owned fork of the MADOS / MariNeXt marine
pollution segmentation codebase and is being brought under NeuralQ
organisation policy. The handbook
[Security & Data Handling Policy](https://github.com/NeuralQ/neuralq-handbook/blob/main/policies/security-and-data.md)
and [Incident Response](https://github.com/NeuralQ/neuralq-handbook/blob/main/policies/incident-response.md)
procedures apply in full.

## Supported versions

Security fixes are provided for the current `main` branch and any actively
supported release line. Older release lines and archived branches receive no
security updates.

| Version / branch | Supported |
| --- | --- |
| `main` | Yes |
| Active release line | Yes |
| Archived or legacy branches | No |

The repository's default branch is being migrated to `main` together with the
rest of the fork's alignment with org policy. Until that migration lands,
treat `main` as the supported branch.

## Reporting a vulnerability

Report suspected vulnerabilities, credential leaks, or exposed data
**privately** to [security@neuralq.ai](mailto:security@neuralq.ai).

**Do not open a public issue or publicly disclose the vulnerability.**

Include:

1. A description of the vulnerability.
2. Steps to reproduce it.
3. The specific system, model, or code path affected.
4. Potential impact or risk assessment.

We acknowledge receipt within 48 hours, triage confidentially, and notify you
when a patch or mitigation has been deployed.

## Project-specific rules

- **Dataset and weights stay external.** MADOS imagery is distributed through
  Zenodo ([https://doi.org/10.5281/zenodo.10664073](https://doi.org/10.5281/zenodo.10664073))
  and the five pretrained MariNeXt checkpoints through a Google Drive folder
  linked from `README.md`. Keep them as links: never commit scene rasters,
  stacked multispectral images, HDF5 tables, `.pth` checkpoints, prediction
  GeoTIFFs, or TensorBoard logs to Git. Only `data/MADOS` is currently listed
  in `.gitignore`, so never `git add` anything from `data/`, `logs/`,
  `marinext/trained_models*/`, `s2sr-data/`, or `notebooks/` — use targeted
  paths instead of `git add -A`.
- **Credentials.** API keys, cloud keys, tokens, and passwords are read from
  environment variables or a secrets manager only. Never hardcode them, never
  commit them. `.env` files are gitignored and must stay local.
- **No secrets in CI.** `.github/workflows/ci.yml` runs with
  `permissions: contents: read`, installs only pinned test dependencies, and
  references no repository secrets. Workflow changes are reviewed like any
  other code change.
- **Dependency hygiene.** Dependency changes go through PR review; the
  training pins live in `requirements.txt` and `environment.yml`, the CI pins
  live in the workflow file.
- **Secret scanning.** Push protection and secret scanning must stay enabled
  on the repository. If a secret is committed, rotate it immediately, then
  treat it as a SEV incident under the handbook incident response procedure.

## Responsible disclosure

Act in good faith to protect the privacy and data of NeuralQ and our clients.
Do not exploit a vulnerability beyond what is necessary to verify its
existence, and do not share details with third parties without written
permission.
