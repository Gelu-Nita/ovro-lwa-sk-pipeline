# OVRO–LWA Two–Stage Spectral Kurtosis (SK) Example  
_A real–data application of pyGSK ≥ 2.1.0_

This folder contains a fully reproducible two–stage **Spectral Kurtosis (SK)** workflow
applied to **OVRO–LWA total–power HDF5 data**, demonstrating how to use the
`pygsk.runtests.run_sk_test` helper for real–instrument pipelines.

This example includes:

- **`ovro-lwa.py`** — command–line application (the main, publishable example)  
- **`ovro_lwa_two_stage_sk_example.ipynb`** — equivalent Jupyter notebook  
  (ideal for exploration, teaching, and iterative analyses)

Both examples implement:

- File autodetection (`basename`, `.h5`, `.hdf5`)
- Automatic extraction of XX/YY streams, frequency axis, and timestamps
- Two–stage SK processing (Stage 1 → Stage 2 via SK renormalization)
- Time–range selection (`--start-idx`, `--ns-max`)
- Optional output (no plots/NPZ saved unless explicitly requested)
- Filename tags encoding **time ranges**, SK parameters, stage, and polarization

---

## 1. Overview of the Two–Stage SK Method

The SK estimator (Nita & Gary 2010) provides robust RFI/outlier detection for
spectral–domain instruments. OVRO–LWA data, like many low–frequency arrays, benefit
from a **two–stage SK approach**:

### **Stage 1**
- Integrates using `(M1, N1, d)`
- Produces first–order SK and flags
- Generates block–summed spectra (`s1`) for Stage 2

### **Stage 2**
- Uses the Stage 1 output `s1` as the new “power”
- Integrates over a much longer effective number of samples:
  ```
  N2 = M1 × N1
  ```
- Produces high–sensitivity SK diagnostics  
- Identifies persistent or subtle bursts, transients, or RFI

Both stages use the same `run_sk_test()` machinery, and both support:
- Histograms
- Context (dynamic spectrum) plots
- Automatic thresholds for given `pfa`
- Verbose diagnostics

---

## 2. File Structure

```
examples/ovro-lwa/
│
├── ovro-lwa.py                             # Command-line interface example
├── ovro_lwa_two_stage_sk_example.ipynb     # Jupyter notebook version
└── README.md                               # (this file)
```

---

## 3. Running the Command-Line Application (`ovro-lwa.py`)

### **Basic usage (no output saved)**

```bash
python ovro-lwa.py <file.h5>
```

Plots are displayed interactively; no files created.

Example:

```bash
python ovro-lwa.py 060963_182827094797b4e9492.h5
```

---

### **Selecting a time range**

Process only the first 50,000 time frames:

```bash
python ovro-lwa.py file.h5 --ns-max 50000
```

Start at index 10000 and read 5000 frames:

```bash
python ovro-lwa.py file.h5 --start-idx 10000 --ns-max 5000
```

The script safely clips ranges so it never exceeds file limits.

---

### **Saving outputs**

Save PNGs:

```bash
python ovro-lwa.py file.h5 --save-plot --outdir results
```

Save NPZ diagnostics:

```bash
python ovro-lwa.py file.h5 --save-npz --outdir results
```

Save both:

```bash
python ovro-lwa.py file.h5 --save-plot --save-npz --outdir results
```

---

### **Full example**

```bash
python ovro-lwa.py 060963_182827094797b4e9492     --pol XX     --M1 64 --M2 8 --N 24     --pfa 1e-3     --start-idx 0 --ns-max 50000     --scale log --cmap magma     --save-plot --save-npz     --outdir results
```

---

## 4. Filename Convention

Output files include:

- HDF5 base name
- Polarization (XX/YY)
- Time range: `t<start>-<stop>`
- Stage (`stage1` or `stage2`)
- SK parameters: `M<M>_N<N>_d<d>`

Example:

```
060963_182827094797b4e9492_XX_t10000-15000_M64_N24_d1.0_stage1_hist.png
```

and:

```
060963_182827094797b4e9492_XX_t10000-15000_M8_N1536_d1.0_stage2_hist.png
```

This makes batch runs self–documenting.

---

## 5. Example Outputs (Stage 1 and Stage 2)

The following figures were generated with:

```bash
python ovro-lwa.py     C:\Users\gelu_\Dropbox\@Projects\ovro-lwa\application\060963_182827094797b4e9492     --pol XX     --start-idx 10000     --ns-max 5000     --scale log     --save-plot
```

Time range:

```
t10000–15000
```

### **Stage 1 Output (M1 = 64, N1 = 24, d = 1)**

![Stage 1](060963_182827094797b4e9492_XX_t10000-15000_M64_N24_d1.0_stage1_hist.png)

---

### **Stage 2 Output (M2 = 8, N2 = 1536, d = 1)**

![Stage 2](060963_182827094797b4e9492_XX_t10000-15000_M8_N1536_d1.0_stage2_hist.png)

---

## 6. Jupyter Notebook Version

**File:** `ovro_lwa_two_stage_sk_example.ipynb`

Features:

- Editable configuration cell  
- Fully documented workflow  
- Inline figures  
- Perfect for experimentation and teaching  

Run it in JupyterLab, Jupyter Notebook, or VS Code.

---

## Batch processing pipeline

The OVRO–LWA example folder includes a small 3-stage SK analysis pipeline:

1. **SK streaming** (`ovro_lwa_sk_stream.py`)
2. **RFI cleaning** (`ovro_lwa_rfi_clean.py`)
3. **Quicklook plotting** (`ovro_lwa_sk_quicklook.py`)

For convenience, there are three batch wrappers and one unified driver:

- `ovro_lwa_batch_stream.py` – run Stage 1 for many raw HDF5 files  
- `ovro_lwa_batch_rfi_clean.py` – run Stage 2 for many `_skstream.h5` files  
- `ovro_lwa_batch_quicklook.py` – run Stage 3 for many SK products  
- `ovro_lwa_batch_pipeline.py` – run all three stages in sequence for each raw file

All batch scripts accept **either**:
- an explicit list of files, and/or  
- an input directory (`--indir`) plus a glob pattern (`--pattern`).

A `--dry-run` flag is available in all batch scripts; it prints the commands
that *would* be executed without actually running them.

### Example: full 3-stage pipeline

From `examples/ovro-lwa/`:

```bash
# Run stream → RFI → quicklook for all files matching 060963_* in the input directory
python ovro_lwa_batch_pipeline.py \
  --indir /nas8/lwa/event-spectrum/typeI1ms \
  --pattern "060963_*" \
  --stream-out ./results \
  --rfi-out ./results \
  --png-out ./png \
  --M 64 --N 24 --d 1.0 --pfa 1e-3 \
  --F-block 8 --flag-mode separate \
  --pol both \
  --scale log --vmin 1e6 --vmax 1e8


## 7. Requirements

- Python ≥ 3.9
- pyGSK ≥ 2.1.0
- NumPy
- Matplotlib
- h5py
- (for notebook) JupyterLab or Jupyter Notebook

---

## 8. Attribution

Based on the Spectral Kurtosis formalism introduced in:

- Nita & Gary (2010), *The Generalized Spectral Kurtosis Estimator*, PASP 122, 595

Developed using the **pyGSK toolkit**:  
https://github.com/suncast-org/pyGSK

---
