# OVRO–LWA SK Pipeline Overview

This documentation describes the **OVRO–LWA Spectral Kurtosis (SK) Pipeline**,
a bottom–up, real–data application of the
[pyGSK – Generalized Spectral Kurtosis Toolkit](https://github.com/suncast-org/pyGSK).

The goal of this repository is to provide a **reproducible, end–to–end workflow**
for SK-based analysis of OVRO–LWA HDF5 data, including:

- A small, tracked **demo dataset** for quick testing
- Standalone **command-line scripts** for single-file and batch processing
- A **two–stage SK workflow** suitable for publication–quality analyses
- **Jupyter notebooks** for exploration, teaching, and iterative development


## Repository Layout (Summary)

At a high level, the repository is organized as follows:

```text
ovro-lwa-sk-pipeline/
├── README.md                     # High-level description and quickstart
├── mkdocs.yml                    # MkDocs configuration for this documentation
├── .github/workflows/            # GitHub Actions (docs deployment)
│
├── configs/                      # YAML configuration files (WIP)
│   └── ovro_lwa_example.yaml
│
├── data/
│   ├── README.md                 # Notes about data organization
│   └── demo/
│       └── ovro_lwa_demo.h5      # 13.5 MB OVRO–LWA demo dataset (tracked)
│
├── docs/                         # This documentation site
│   ├── pipeline_overview.md      # (this file)
│   └── ovro_lwa_readme.md        # Two–stage SK example documentation
│
├── figures/
│   ├── 060963_..._stage1_hist.png
│   └── 060963_..._stage2_hist.png
│
├── notebooks/
│   ├── ovro_lwa_single_file_pipeline_demo.ipynb
│   └── ovro_lwa_two_stage_sk_example.ipynb
│
└── scripts/
    ├── ovro-lwa.py
    ├── ovro_lwa_sk_quicklook.py
    ├── ovro_lwa_sk_stream.py
    ├── ovro_lwa_rfi_clean.py
    ├── ovro_lwa_batch_pipeline.py
    ├── ovro_lwa_batch_quicklook.py
    ├── ovro_lwa_batch_rfi_clean.py
    ├── ovro_lwa_batch_stream.py
    ├── ovro_lwa_batch_twostage.py
    ├── make_ovro_lwa_segment.py
    ├── inspect_h5.py
    └── run_ovro_lwa_sk_pipeline.py  # High-level driver (placeholder)
```

For details of the two–stage SK method and example outputs,
see the separate page **“Two–Stage SK Example”** in the navigation.



## Demo Dataset

A small OVRO–LWA total–power HDF5 file is included to allow running the
pipeline immediately after cloning the repository.

**Path:**

```text
data/demo/ovro_lwa_demo.h5
```

Characteristics:

- Size: ~13.5 MB
- Format: OVRO–LWA HDF5
- Contains: A short time–frequency segment suitable for SK thresholding,
  RFI detection, and quicklook generation.
- Intended use: quick testing of scripts and notebooks, CI-style smoke tests,
  and demonstrations on systems without access to large raw data volumes.

The `.gitignore` rules are configured so that **only this demo file is tracked**.
All other HDF5/FITS/NPZ products placed under `data/` remain untracked unless
explicitly whitelisted.



## Core Scripts and Workflows

The pipeline is structured around three conceptual stages:

1. **Streaming SK computation** – compute SK over chunks of the dynamic spectrum.
2. **RFI cleaning / flagging** – apply SK-based thresholds and generate masks.
3. **Quicklook products** – create diagnostic histograms and context plots.

The following scripts implement these stages and their batch wrappers:

- `ovro_lwa_sk_stream.py` – Stage 1 SK processing for a single file
- `ovro_lwa_rfi_clean.py` – Stage 2 SK / RFI cleaning
- `ovro_lwa_sk_quicklook.py` – quicklook plotting for SK products
- `ovro_lwa_batch_stream.py` – Stage 1 over many files
- `ovro_lwa_batch_rfi_clean.py` – Stage 2 over many SK products
- `ovro_lwa_batch_quicklook.py` – quicklook plots for many SK products
- `ovro_lwa_batch_pipeline.py` – convenience driver that runs all three stages
- `ovro-lwa.py` – a “classic” two–stage SK example, also mirrored in a notebook

Additional helpers:

- `make_ovro_lwa_segment.py` – create trimmed segments from larger files
- `inspect_h5.py` – quick inspection of OVRO–LWA HDF5 file structure
- `run_ovro_lwa_sk_pipeline.py` – high-level wrapper (to be expanded)



## Notebooks

Two notebooks mirror and complement the command-line workflows:

- **`ovro_lwa_single_file_pipeline_demo.ipynb`**  
  End-to-end SK analysis of the demo file, using the local `data/demo/` dataset.

- **`ovro_lwa_two_stage_sk_example.ipynb`**  
  Full two–stage SK example equivalent to `ovro-lwa.py`,
  ideal for exploration and teaching.

These are designed to run **out of the box** with the included demo file,
assuming `pyGSK` and other dependencies are installed.



## Installation and Environment

A typical setup might look like:

```bash
git clone https://github.com/Gelu-Nita/ovro-lwa-sk-pipeline.git
cd ovro-lwa-sk-pipeline

conda create -n ovro-lwa-sk python=3.11
conda activate ovro-lwa-sk

pip install pygsk numpy scipy matplotlib astropy h5py pyyaml
```

On systems like `pipeline`, you may also define convenience variables:

```bash
export OVRO_LWA_SK_HOME="$HOME/lwa/ovro-lwa-sk-pipeline"
export PATH="$OVRO_LWA_SK_HOME/scripts:$PATH"
```

so that scripts like `ovro_lwa_sk_quicklook.py` can be run from any directory.



## Minimal Example Run

After installation, a minimal quicklook run on the demo file might be:

```bash
ovro_lwa_sk_quicklook.py data/demo/ovro_lwa_demo.h5
```

or, explicitly specifying `python`:

```bash
python scripts/ovro_lwa_sk_quicklook.py data/demo/ovro_lwa_demo.h5
```

More advanced usage (two–stage SK, batch processing, etc.) is described in
the **Two–Stage SK Example** page and in the script docstrings.



## Relationship to pyGSK and SUNCAST

This repository is intended as an **application-level companion** to
`pyGSK`, not as a replacement:

- All SK calculations are performed by `pyGSK`.
- This code focuses on **OVRO–LWA–specific data handling** and workflow glue.
- The repository is a **bottom–up prototype** that may later inform
  SUNCAST-hosted workflows and examples.

When the pipeline matures, the intention is to:
- propose selected components for inclusion in SUNCAST workflows, and
- register a Zenodo record once the repository is transferred to
  the `suncast-org` GitHub organization.
