#!/usr/bin/env python3
"""
ovro_lwa_batch_pipeline.py

Unified batch pipeline for OVRO-LWA SK analysis:

For each input *raw* OVRO-LWA HDF5 file:

  1) Run SK streaming (dual-pol) with ovro_lwa_sk_stream.py
     → produces <results_out>/<base>_skstream.h5

  2) Run quicklook on the SK-stream product (Stage 1)
     → produces <png_out>/<base>_skstream_*.png

  3) Run RFI cleaning with ovro_lwa_rfi_clean.py
     → produces <results_out>/<base>_skstream_rfi_M<M>_F<F_block>_<flag_mode>.h5

  4) Run quicklook on the RFI-clean product
     → produces <png_out>/<base>_skstream_rfi_M<M>_F<F_block>_<flag_mode>_*.png

This script is designed to orchestrate the three building blocks you
already have (stream, clean, quicklook), and to ensure that BOTH
Stage-1 (SK stream) and Stage-2 (RFI clean) PNG plots are produced.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import subprocess
from typing import List, Optional


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _find_inputs(files: List[str], indir: Optional[str], pattern: str) -> List[str]:
    """
    Build the list of raw HDF5 inputs.

    Priority:
      1) Explicit positional files, if any (they must exist).
      2) Otherwise, glob(indir/pattern).
    """
    inputs: List[str] = []

    # 1) Explicit files
    for f in files:
        if os.path.exists(f):
            inputs.append(os.path.abspath(f))
        else:
            print(f"[WARN] Positional file not found, skipping: {f}")

    # 2) If none provided, use indir + pattern
    if not inputs and indir:
        pattern_path = os.path.join(indir, pattern)
        globbed = sorted(glob.glob(pattern_path))
        inputs.extend(os.path.abspath(p) for p in globbed)

    if not inputs:
        raise SystemExit(
            "No input files found. Provide positional files and/or "
            "--indir / --pattern."
        )

    return inputs


def _run(cmd: List[str]) -> None:
    """Run a subprocess command with basic logging."""
    print(f"[CMD] {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def _base_from_raw(path: str) -> str:
    """Strip directory and extension to get base name."""
    base = os.path.basename(path)
    root, _ext = os.path.splitext(base)
    return root


# ----------------------------------------------------------------------
# Main orchestrator
# ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Batch OVRO-LWA SK pipeline: stream → quicklook (stage1) → "
            "RFI clean → quicklook (RFI)."
        )
    )

    # Inputs
    ap.add_argument(
        "files",
        nargs="*",
        help="Raw OVRO-LWA HDF5 files to process (if omitted, use --indir/--pattern).",
    )
    ap.add_argument(
        "--indir",
        type=str,
        default=None,
        help="Directory containing raw HDF5 files (used if no positional files).",
    )
    ap.add_argument(
        "--pattern",
        type=str,
        default="*",
        help="Glob pattern within --indir (default: '*').",
    )

    # Output locations
    ap.add_argument(
        "--results-out",
        type=str,
        default="./results",
        help="Directory for SK-stream and RFI-clean HDF5 outputs (default: ./results).",
    )
    ap.add_argument(
        "--png-out",
        type=str,
        default="./png",
        help="Directory for PNG quicklook outputs (default: ./png).",
    )

    # Streaming (Stage 1) parameters
    ap.add_argument("--M", type=int, default=64, help="Block size M for SK streaming (default: 64).")
    ap.add_argument("--N", type=int, default=24, help="Number of spectra per block N (default: 24).")
    ap.add_argument("--d", type=float, default=1.0, help="Shape parameter d for SK (default: 1.0).")
    ap.add_argument(
        "--pfa", type=float, default=1e-3,
        help="One-sided probability of false alarm (default: 1e-3)."
    )
    ap.add_argument(
        "--start-idx",
        type=int,
        default=0,
        help="Starting time index for streaming (default: 0).",
    )
    ap.add_argument(
        "--ns-max",
        type=int,
        default=None,
        help="Optional maximum number of time frames to read (default: all).",
    )

    # RFI-clean parameters
    ap.add_argument(
        "--F-block",
        type=int,
        default=8,
        help="Number of adjacent frequency channels per RFI block (default: 8).",
    )
    ap.add_argument(
        "--flag-mode",
        choices=["separate", "or", "and"],
        default="separate",
        help=(
            "How to combine XX/YY flags: "
            "'separate' (default), 'or', or 'and'."
        ),
    )

    # Quicklook parameters (shared by Stage1 + RFI plots)
    ap.add_argument(
        "--pol",
        choices=["XX", "YY", "both"],
        default="both",
        help="Polarization(s) to plot in quicklook figures (default: both).",
    )
    ap.add_argument(
        "--scale",
        choices=["linear", "log"],
        default="log",
        help="Scaling for S1 panels in quicklook (default: log).",
    )
    ap.add_argument(
        "--vmin",
        type=float,
        default=None,
        help="vmin for S1 color scale (default: auto).",
    )
    ap.add_argument(
        "--vmax",
        type=float,
        default=None,
        help="vmax for S1 color scale (default: auto).",
    )
    ap.add_argument(
        "--log-eps",
        type=float,
        default=None,
        help="Floor value for log scaling in S1 panels (default: auto).",
    )
    ap.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="DPI for saved PNGs (default: 150).",
    )
    ap.add_argument(
        "--transparent",
        action="store_true",
        help="Save PNGs with transparent background.",
    )
    ap.add_argument(
        "--no-show",
        action="store_true",
        help="Do not attempt to show figures (recommended on headless systems).",
    )

    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done, but do not run any commands.",
    )

    args = ap.parse_args()

    # Prepare input list
    inputs = _find_inputs(args.files, args.indir, args.pattern)
    results_out = os.path.abspath(args.results_out)
    png_out = os.path.abspath(args.png_out)

    os.makedirs(results_out, exist_ok=True)
    os.makedirs(png_out, exist_ok=True)

    print("============================================================")
    print(f"[INFO] Batch pipeline starting on {len(inputs)} file(s).")
    print(f"[INFO] Results HDF5 directory: {results_out}")
    print(f"[INFO] PNG output directory : {png_out}")
    print("============================================================")

    # Loop over each raw input file
    for raw_path in inputs:
        base = _base_from_raw(raw_path)
        print("============================================================")
        print(f"[INFO] Processing raw file: {raw_path}")
        print("------------------------------------------------------------")

        # ---------------------------------------------------------
        # 1) Stage 1: SK streaming → *_skstream.h5
        # ---------------------------------------------------------
        skstream_out = os.path.join(results_out, f"{base}_skstream.h5")

        stream_cmd = [
            sys.executable,
            "ovro_lwa_sk_stream.py",
            raw_path,
            "--M", str(args.M),
            "--N", str(args.N),
            "--d", str(args.d),
            "--pfa", str(args.pfa),
            "--start-idx", str(args.start_idx),
            "--out", skstream_out,
        ]
        if args.ns_max is not None:
            stream_cmd.extend(["--ns-max", str(args.ns_max)])

        print(f"[INFO] [Stage 1] Streaming to: {skstream_out}")
        if not args.dry_run:
            _run(stream_cmd)

        # ---------------------------------------------------------
        # 2) Stage 1 quicklook on *_skstream.h5
        # ---------------------------------------------------------
        print("[INFO] [Stage 1] Quicklook for SK-stream product...")
        ql1_cmd = [
            sys.executable,
            "ovro_lwa_sk_quicklook.py",
            skstream_out,
            "--pol", args.pol,
            "--scale", args.scale,
            "--save-plot", "png",
            "--out", png_out,
        ]
        if args.vmin is not None:
            ql1_cmd.extend(["--vmin", str(args.vmin)])
        if args.vmax is not None:
            ql1_cmd.extend(["--vmax", str(args.vmax)])
        if args.log_eps is not None:
            ql1_cmd.extend(["--log-eps", str(args.log_eps)])
        if args.transparent:
            ql1_cmd.append("--transparent")
        if args.no_show:
            ql1_cmd.append("--no-show")

        if not args.dry_run:
            _run(ql1_cmd)

        # ---------------------------------------------------------
        # 3) Stage 2: RFI cleaning → *_skstream_rfi_...h5
        # ---------------------------------------------------------
        print("[INFO] [Stage 2] RFI cleaning...")
        rfi_cmd = [
            sys.executable,
            "ovro_lwa_rfi_clean.py",
            skstream_out,
            "--F-block", str(args.F_block),
            "--flag-mode", args.flag_mode,
            "--out", results_out,
        ]
        if not args.dry_run:
            _run(rfi_cmd)

        # We know the naming convention from rfi_clean:
        # <base>_skstream_rfi_M<M>_F<F_block>_<flag_mode>.h5
        rfi_out = os.path.join(
            results_out,
            f"{base}_skstream_rfi_M{args.M}_F{args.F_block}_{args.flag_mode}.h5",
        )
        print(f"[INFO] [Stage 2] RFI-clean product: {rfi_out}")

        # ---------------------------------------------------------
        # 4) Stage 2 quicklook on RFI-clean product
        # ---------------------------------------------------------
        print("[INFO] [Stage 2] Quicklook for RFI-clean product...")
        ql2_cmd = [
            sys.executable,
            "ovro_lwa_sk_quicklook.py",
            rfi_out,
            "--pol", args.pol,
            "--scale", args.scale,
            "--save-plot", "png",
            "--out", png_out,
        ]
        if args.vmin is not None:
            ql2_cmd.extend(["--vmin", str(args.vmin)])
        if args.vmax is not None:
            ql2_cmd.extend(["--vmax", str(args.vmax)])
        if args.log_eps is not None:
            ql2_cmd.extend(["--log-eps", str(args.log_eps)])
        if args.transparent:
            ql2_cmd.append("--transparent")
        if args.no_show:
            ql2_cmd.append("--no-show")

        if not args.dry_run:
            _run(ql2_cmd)

        print(f"[INFO] Finished file: {raw_path}")

    print("============================================================")
    print("[INFO] Batch pipeline complete.")
    print("============================================================")


if __name__ == "__main__":
    main()
