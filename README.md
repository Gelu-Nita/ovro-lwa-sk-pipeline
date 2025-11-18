# OVRO–LWA Spectral Kurtosis (SK) Pipeline

**Author:** Gelu M. Nita  
**Last updated:** 2025-11-18

This repository provides a fully reproducible, bottom–up implementation of an
end-to-end **Spectral Kurtosis (SK)** pipeline for **OVRO–LWA** total-power HDF5 data.
It functions as an application-level companion to:

👉 **pyGSK – Generalized Spectral Kurtosis Toolkit**  
https://github.com/suncast-org/pyGSK

The goal of this repository is to demonstrate how to apply `pyGSK` to real
OVRO–LWA data using a documented, transparent scientific workflow.

---

# 📘 **Full Documentation**

The complete documentation (overview, examples, figures, installation notes)
is available online via GitHub Pages:

👉 **https://gelu-nita.github.io/ovro-lwa-sk-pipeline/**

This site is automatically generated from the `docs/` folder using **MkDocs
(Material theme)** and is kept up to date with every `main` branch push.

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

Equivalent if you added the scripts/ folder to PATH:

```
ovro_lwa_sk_quicklook.py data/demo/ovro_lwa_demo.h5
```

More examples (two-stage SK, batch processing, plotting conventions) are in:

👉 `docs/ovro_lwa_readme.md`  
👉 `notebooks/ovro_lwa_two_stage_sk_example.ipynb`

---

# 🎓 Relationship to pyGSK and SUNCAST

- All SK calculations rely on `pyGSK`.
- This repository focuses on **OVRO–LWA–specific pipelines**.
- It is designed as a **prototype** that may later be transferred to  
  the **SUNCAST organization**.
- A Zenodo DOI will be created after migration.

---

# 📜 License

BSD 3-Clause License (see `LICENSE`).