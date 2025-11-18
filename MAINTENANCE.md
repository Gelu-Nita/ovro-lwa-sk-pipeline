# Maintenance and Governance

## Lead Maintainer

- **Name:** Gelu M. Nita  
- **Role:** Lead developer and maintainer  
- **Scope:** Overall design of the OVRO–LWA SK pipeline, integration with
  `pyGSK`, documentation, and release strategy.

## Repository Scope

This repository is intended as a **personal development space** for an
OVRO–LWA Spectral Kurtosis pipeline, to be used as a bottom–up model for:

- Demonstrating how to apply `pyGSK` to real telescope data.
- Prototyping workflows that may later be adopted under the SUNCAST
  organization (e.g., as `pyGSK` examples or related workflow repos).
- Providing a reproducible, documented environment for SK-based RFI
  detection and analysis.

## Maintenance Model

Initially, maintenance follows a **single–maintainer** model:

- All changes are curated by the lead maintainer.
- External contributions (if any) are reviewed on a best-effort basis.
- The repository may evolve rapidly and break compatibility between
  commits; users are encouraged to rely on tagged versions once they exist.

As the project matures, this model can evolve into a more distributed
governance, including:

- Designated co-maintainers.
- Formal review of pull requests.
- Stable branches for “released” workflows (e.g., `main` or `stable`)
  and feature branches for experimental work.

## Branching and Tagging (Suggested)

- `main` (or `master`): stable, curated branch.
- `dev/…`: feature branches for experimental changes
  (e.g., `dev/ovro-lwa-thresholds`, `dev/notebook-updates`).
- Tags (e.g., `v0.1.0`, `v0.2.0`) to mark important milestones that may be
  referenced from papers, documentation, or Zenodo archives.

## Long-Term Plans

If and when parts of this repository are adopted into the SUNCAST
ecosystem, this repo can:

- Continue as a personal sandbox for prototype workflows, or
- Transition into an archived state with a clear pointer to the official,
  community-maintained successor repository.

In either case, maintenance decisions should prioritize reproducibility,
traceability of scientific results, and clarity for future users.
