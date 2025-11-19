# OVRO–LWA Spectral Kurtosis (SK) Pipeline

[![Docs](https://img.shields.io/badge/docs-online-blue?style=flat-square)](https://gelu-nita.github.io/ovro-lwa-sk-pipeline/)

📘 **Full documentation:**  
https://gelu-nita.github.io/ovro-lwa-sk-pipeline/

**Author:** Gelu M. Nita  
**Last updated:** 2025-11-18

This repository provides a fully reproducible, bottom–up implementation of an
end-to-end **Spectral Kurtosis (SK)** pipeline for **OVRO–LWA** total-power HDF5 data.
It serves as an application-level companion to:

👉 **pyGSK – Generalized Spectral Kurtosis Toolkit**  
https://github.com/suncast-org/pyGSK

The goal is to demonstrate how to apply `pyGSK` to real OVRO–LWA data using a
transparent, documented scientific workflow.

---

# 📘 Documentation

Full documentation and examples are available at:

👉 **https://gelu-nita.github.io/ovro-lwa-sk-pipeline/**

This site is automatically generated from the `docs/` folder using **MkDocs
(Material theme)**.

---

# 📁 Repository Structure

```
ovro-lwa-sk-pipeline/
├── README.md
├── mkdocs.yml                     # Documentation config
├── .github/workflows/
│   └── publish-docs.yml           # GitHub Pages deploy workflow
│
├── configs/
│   └── ovro_lwa_example.yaml
│
├── data/
│   ├── README.md
│   └── demo/
│       └── ovro_lwa_demo.h5        # 13.5 MB demo file (tracked)
│
├── docs/
│   ├── pipeline_overview.md        # High-level pipeline overview
│   └── ovro_lwa_readme.md          # Two-stage SK example documentation
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
    ├── ovro_lwa_sk_stream.py
    ├── ovro_lwa_rfi_clean.py
    ├── ovro_lwa_sk_quicklook.py
    ├── ovro_lwa_batch_stream.py
    ├── ovro_lwa_batch_rfi_clean.py
    ├── ovro_lwa_batch_quicklook.py
    ├── ovro_lwa_batch_pipeline.py
    ├── ovro_lwa_batch_twostage.py
    ├── make_ovro_lwa_segment.py
    ├── inspect_h5.py
    └── run_ovro_lwa_sk_pipeline.py
```

---

# 📦 Installation

```
git clone https://github.com/Gelu-Nita/ovro-lwa-sk-pipeline
cd ovro-lwa-sk-pipeline

conda create -n ovro-lwa-sk python=3.11
conda activate ovro-lwa-sk

pip install pygsk numpy scipy matplotlib h5py astropy pyyaml
```

---

# ▶️ Quick Start Example

Run a quicklook SK plot on the included demo file:

```
python scripts/ovro_lwa_sk_quicklook.py data/demo/ovro_lwa_demo.h5
```

If the scripts folder is added to PATH:

```
ovro_lwa_sk_quicklook.py data/demo/ovro_lwa_demo.h5
```

More detailed workflows (two-stage SK, batch pipelines) are documented here:

- `docs/ovro_lwa_readme.md`
- `notebooks/ovro_lwa_two_stage_sk_example.ipynb`

---

# 🎓 Relationship to pyGSK and SUNCAST

- All SK calculations rely on `pyGSK`.
- This repository focuses on **OVRO–LWA–specific pipelines and workflow glue**.
- It is designed as a **prototype** for eventual migration under SUNCAST.
- A Zenodo DOI will be created once the repository is transferred.

---

# 📜 License

BSD 3-Clause License (see `LICENSE`).
