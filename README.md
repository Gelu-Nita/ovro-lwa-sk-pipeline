# OVRO–LWA SK Pipeline

**Status:** Personal development repository (bottom–up model)  
**Author:** Gelu M. Nita  
**Last updated:** 2025-11-16

This repository contains a *bottom–up* development of an end–to–end
Spectral Kurtosis (SK) analysis pipeline for **OVRO–LWA** solar data.
It is designed as an application–level companion to the
[`pyGSK` – Generalized Spectral Kurtosis Toolkit](https://github.com/suncast-org/pyGSK),
showing how to use `pyGSK` on real telescope data in a
reproducible, fully documented workflow.

The primary goals are:

- Provide a concrete **OVRO–LWA SK pipeline** that can be cloned and run
  by interested users.
- Demonstrate **good open–science practices** (version control,
  documentation, configuration files, and reproducible runs).
- Serve as a **bottom–up model** that can later be transferred or
  adapted for inclusion under the SUNCAST organization.

This repository is **not** intended for PyPI distribution.
Instead, users clone it directly and install dependencies such as `pyGSK`
in their own Python environment.

---

## Repository Layout

```text
ovro-lwa-sk-pipeline/
├── README.md
├── LICENSE
├── CODE_OF_CONDUCT.md
├── MAINTENANCE.md
├── CONTRIBUTING.md
├── .gitignore
├── scripts/
│   └── run_ovro_lwa_sk_pipeline.py        # main driver script (to be developed)
├── notebooks/
│   └── ovro_lwa_sk_demo.ipynb             # exploratory / demo notebooks
├── data/
│   └── README.md                          # notes on expected data formats (no data tracked)
├── configs/
│   └── ovro_lwa_example.yaml              # example configuration file (to be developed)
├── docs/
│   └── pipeline_overview.md               # extended documentation (to be developed)
└── figures/
    └── .gitkeep                           # placeholder for generated plots
```

At this stage, most files are **skeletons/placeholders** to define the
intended structure. They can be refined as the pipeline matures.

---

## Dependencies

The exact dependency list will evolve, but the core assumptions are:

- Python ≥ 3.9
- [`pyGSK`](https://github.com/suncast-org/pyGSK) (installed from PyPI or GitHub)
- `numpy`, `scipy`
- `matplotlib`
- `astropy` (for time handling, units, etc.)
- `h5py` or similar I/O package (depending on OVRO–LWA data format)
- `yaml` (`pyyaml`) for configuration files

Once the pipeline stabilizes, these will be consolidated into a
`requirements.txt` or `environment.yml` file.

---

## Installation

1. **Clone this repository** (from your personal GitHub account):

   ```bash
   git clone https://github.com/<your-username>/ovro-lwa-sk-pipeline.git
   cd ovro-lwa-sk-pipeline
   ```

2. **Create and activate a Python environment** (example using `conda`):

   ```bash
   conda create -n ovro-lwa-sk python=3.11
   conda activate ovro-lwa-sk
   ```

3. **Install `pyGSK` and other dependencies**:

   ```bash
   pip install pygsk numpy scipy matplotlib astropy h5py pyyaml
   ```

   (Adjust this list as we refine the pipeline.)

---

## Usage (planned)

A typical run is envisioned as:

```bash
python scripts/run_ovro_lwa_sk_pipeline.py \\
    /path/to/ovro_lwa/data \\
    --config configs/ovro_lwa_example.yaml \\
    --output-dir ./figures \\
    --save-intermediate
```

The driver script will:

1. Load configuration options (data selection, SK parameters, thresholds).
2. Prepare the data in a form suitable for `pyGSK` (time–frequency arrays,
   integration parameters, etc.).
3. Call `pyGSK` routines to compute SK, apply thresholds, and flag RFI.
4. Produce summary plots and simple text/CSV reports.

At the moment, the script is a placeholder and will be developed iteratively.

---

## Relationship to `pyGSK` and SUNCAST

- This repository **depends** on `pyGSK` but does not modify it.
- It serves as a **bottom–up, real–data application** that complements the
  top–down design of `pyGSK` examples.
- The intent is that, once matured, selected parts (scripts, configs,
  documentation) can be proposed for inclusion under the
  **SUNCAST GitHub organization**, e.g., within a dedicated
  `examples/ovro-lwa/` tree in `pyGSK` or a related SUNCAST workflow repo.

---

## Contributing and Maintenance

Since this is a personal development repo, contributions are initially
limited and curated. As the project evolves, we may:

- Open issues for feature requests and bug reports.
- Accept pull requests following the guidelines in `CONTRIBUTING.md`.
- Define a clearer maintainer model in `MAINTENANCE.md`.

Please also see `CODE_OF_CONDUCT.md` for expectations regarding respectful,
inclusive collaboration.

---

## License

This repository is released under the **BSD 3-Clause License** (see `LICENSE`).

