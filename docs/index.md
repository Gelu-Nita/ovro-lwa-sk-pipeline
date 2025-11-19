# OVRO–LWA Spectral Kurtosis (SK) Pipeline

A research-grade, end-to-end Spectral Kurtosis (SK) analysis workflow for  
**OVRO–LWA total-power data**, built on top of the  
[`pyGSK`](https://github.com/suncast-org/pyGSK) toolkit.

This documentation provides:

- A high-level overview of the SK pipeline design
- A fully reproducible two-stage SK example using real OVRO–LWA data
- Links to scripts, notebooks, and configuration files included in the repository

---

## 🚀 What This Pipeline Provides

- **Single-file SK analysis** (`ovro-lwa.py`)  
- **Two-stage SK processing** based on the generalized SK estimator  
- **Batch-mode pipelines** for large OVRO–LWA datasets  
- **Quicklook visualization tools** for dynamic spectra and SK histograms  
- **A demo HDF5 dataset** included directly in the repository for testing

The pipeline is intended as a *bottom-up development model* that will
ultimately integrate into broader open-science workflows under the
**SUNCAST** initiative.

---

## 📄 Documentation Sections

### 🔹 [Pipeline Overview](pipeline_overview.md)
Conceptual description of the workflow, SK methodology, data flow, and architecture.

### 🔹 [Two-Stage SK Example](ovro_lwa_readme.md)
Detailed, real-data worked example with scripts and notebook versions.

---

## 📦 Repository Highlights

- **Scripts:** full command-line tools for SK streaming, renormalization, cleaning, and plotting  
- **Notebooks:** demonstration workflows suitable for exploration and teaching  
- **Configs:** ready-to-modify YAML templates  
- **Data:** a built-in OVRO–LWA demo HDF5 file for immediate testing  
- **Figures:** example output plots  

---

## 🔧 Requirements

- Python ≥ 3.9  
- `pyGSK` ≥ 2.1.0  
- `numpy`, `matplotlib`, `h5py`, `yaml`  
- (optional) JupyterLab  

Full details are provided in the main repository `README.md`.

---

## 📫 Feedback & Contributions

This repository is under active development.  
Issues and suggestions are welcome through the GitHub issue tracker.

---

## 🔗 External Links

- **pyGSK Toolkit:** https://github.com/suncast-org/pyGSK  
- **OVRO–LWA Observatory:** https://www.ovro.caltech.edu/lwa  
