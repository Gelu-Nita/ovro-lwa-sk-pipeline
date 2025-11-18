# OVRO–LWA SK Pipeline
**Author:** Gelu M. Nita  
**Last updated:** 2025-11-16

This repository contains a *bottom–up* development of an end–to–end  
Spectral Kurtosis (SK) analysis pipeline for **OVRO–LWA** solar data.  
It is designed as an application–level companion to  
[`pyGSK` – Generalized Spectral Kurtosis Toolkit](https://github.com/suncast-org/pyGSK),  
demonstrating how to apply `pyGSK` to real telescope data in a reproducible,  
fully documented workflow.

The goals of this repository are:

- Provide a concrete **OVRO–LWA SK analysis pipeline** that users can clone and run.
- Showcase **open-science best practices**, including configuration-driven workflows,
  version control organization, and reproducibility.
- Serve as a **bottom-up model** for future adoption within the  
  **SUNCAST GitHub organization**.

This repository is **not** intended for PyPI distribution.  
Users clone it directly and install dependencies manually.

---

## Repository Contents

```
ovro-lwa-sk-pipeline/
├── .gitignore
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── MAINTENANCE.md
├── README.md
│
├── configs/
│   └── ovro_lwa_example.yaml                # Example configuration file (work in progress)
│
├── data/
│   ├── README.md                            # Documentation of the dataset structure
│   └── demo/
│       └── ovro_lwa_demo.h5                 # 13.5 MB example OVRO–LWA dataset (tracked)
│
├── docs/
│   ├── ovro_lwa_readme.md                   # Detailed OVRO–LWA example documentation
│   └── pipeline_overview.md                 # High-level description of the pipeline
│
├── figures/
│   ├── .gitkeep                             # Keep directory in Git
│   ├── 060963_182827094797b4e9492_XX_t10000-15000_M64_N24_d1.0_stage1_hist.png
│   └── 060963_182827094797b4e9492_XX_t10000-15000_M8_N1536_d1.0_stage2_hist.png
│
├── notebooks/
│   ├── ovro_lwa_single_file_pipeline_demo.ipynb
│   └── ovro_lwa_two_stage_sk_example.ipynb
│
└── scripts/
    ├── inspect_h5.py
    ├── make_ovro_lwa_segment.py
    ├── ovro-lwa.py
    ├── ovro_lwa_batch_pipeline.py
    ├── ovro_lwa_batch_quicklook.py
    ├── ovro_lwa_batch_rfi_clean.py
    ├── ovro_lwa_batch_stream.py
    ├── ovro_lwa_batch_twostage.py
    ├── ovro_lwa_rfi_clean.py
    ├── ovro_lwa_sk_quicklook.py
    ├── ovro_lwa_sk_stream.py
    └── run_ovro_lwa_sk_pipeline.py          # High-level driver script (placeholder)
```

---

## Demo Dataset

A small OVRO–LWA dataset is included to allow running the notebooks and scripts  
immediately, without needing separate downloads.

**File:**  
```
data/demo/ovro_lwa_demo.h5
```

**Details:**

- Size: ~13.5 MB  
- Format: OVRO–LWA HDF5 (standard telescope structure)  
- Contains: A short time–frequency segment suitable for  
  SK thresholding, two-stage SK analysis, RFI classification,  
  and quicklook development.

Only this single demo file is tracked.  
All other data files placed under the `data` directory are ignored by default:

```gitignore
data/**/*.h5
!data/demo/ovro_lwa_demo.h5
```

Users are encouraged to place their own OVRO–LWA files under `data/`,  
where they will remain untracked by Git.

---

## Notebooks

Two demonstration notebooks are provided:

### `ovro_lwa_single_file_pipeline_demo.ipynb`
- SK analysis on a single HDF5 file  
- Quicklook visualizations  
- RFI classification workflow

### `ovro_lwa_two_stage_sk_example.ipynb`
- Two–stage SK estimation workflow  
- M,N parameter sweep → refined SK thresholds  
- Comparison plots and diagnostic visualizations

---

## Scripts

The `scripts` directory contains standalone tools and batch pipelines for:

- inspecting OVRO–LWA HDF5 files  
- extracting shorter time–frequency segments  
- computing SK for single or multiple files  
- generating SK quicklooks  
- batch processing pipelines  
- two–stage SK analysis  
- experimental streaming/real-time pipelines

These scripts were originally prototyped in a `pyGSK` fork and are now  
maintained independently in this repository.

---

## Installation

```bash
git clone https://github.com/<your-username>/ovro-lwa-sk-pipeline.git
cd ovro-lwa-sk-pipeline
```

Create environment:

```bash
conda create -n ovro-lwa-sk python=3.11
conda activate ovro-lwa-sk
```

Install dependencies:

```bash
pip install pygsk numpy scipy matplotlib astropy h5py pyyaml
```

---

## Usage

**Example high-level workflow (planned):**

```bash
python scripts/run_ovro_lwa_sk_pipeline.py     /path/to/ovro_lwa/data     --config configs/ovro_lwa_example.yaml     --output-dir ./figures     --save-intermediate
```

The demo dataset can be used to test the notebooks and scripts immediately, e.g.:

```bash
python scripts/ovro_lwa_sk_quicklook.py data/demo/ovro_lwa_demo.h5
```

---

## Relationship to `pyGSK` and SUNCAST

- This repository **depends on `pyGSK`** for SK calculations and thresholding.  
- It serves as a real-data, application-level example complementing  
  the top-down design of `pyGSK`.  
- Stable components may later be migrated to the  
  **SUNCAST GitHub organization**.

---

## License

Released under the **BSD 3-Clause License**.
