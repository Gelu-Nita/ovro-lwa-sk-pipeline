# Data Directory

This directory contains the input data used by the OVRO–LWA SK pipeline.

## Demo Dataset

A small example file is provided for testing and demonstration:

demo/ovro_lwa_demo.h5

- Size: ~13.5 MB  
- Purpose: Allows running the notebooks and scripts without requiring access to
  the full OVRO–LWA archive.
- Contents: A short time–frequency segment extracted from a real OVRO–LWA observation,
  suitable for SK analysis examples, thresholding demonstrations, and quicklook testing.

## Notes

- Larger OVRO–LWA files are **intentionally not stored** in this repository.
- The `.gitignore` rules ensure that only the demo file is tracked, while preventing
  accidental commits of large telescope datasets.
- Users wishing to run the pipeline on full-resolution OVRO–LWA data should place
  their files under the `data/` directory but ensure they are excluded from Git.


