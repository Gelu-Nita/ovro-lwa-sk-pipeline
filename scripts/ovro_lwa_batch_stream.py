#!/usr/bin/env python3
"""
ovro_lwa_batch_stream.py

Batch wrapper around ovro_lwa_sk_stream.py

Usage examples
--------------
# Process explicit list of raw OVRO-LWA files
python ovro_lwa_batch_stream.py \
    /nas8/lwa/event-spectrum/typeI1ms/060963_182827094797b4e9492 \
    /nas8/lwa/event-spectrum/typeI1ms/060963_182221509087db0347f \
    --outdir ./results

# Process all files in a directory matching pattern
python ovro_lwa_batch_stream.py \
    --indir /nas8/lwa/event-spectrum/typeI1ms \
    --pattern "060963_*" \
    --outdir ./results
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from typing import List


def _collect_inputs(files: List[str], indir: str | None, pattern: str) -> List[str]:
    paths: List[str] = []

    # Explicit files
    for f in files:
        if os.path.exists(f):
            paths.append(os.path.abspath(f))
        else:
            print(f"[WARN] Input file not found, skipping: {f}")

    # From directory + pattern
    if indir is not None:
        indir = os.path.abspath(indir)
        glob_pattern = os.path.join(indir, pattern)
        found = sorted(glob.glob(glob_pattern))
        if not found:
            print(f"[WARN] No files matched pattern '{glob_pattern}'")
        else:
            paths.extend(found)

    # Make unique, preserve order
    seen = set()
    uniq = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    return uniq


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch SK streaming (ovro_lwa_sk_stream.py) for OVRO-LWA HDF5 files."
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Raw OVRO-LWA files (with or without .h5/.hdf5 extension).",
    )
    parser.add_argument(
        "--indir",
        type=str,
        default=None,
        help="Directory to scan for input files (used together with --pattern).",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*",
        help="Glob pattern within --indir (default: '*').",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        required=True,
        help="Output directory for _skstream.h5 results.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the commands that would be run, but do not execute them.",
    )

    # Forwarded SK-stream options (mirroring ovro_lwa_sk_stream.py)
    parser.add_argument("--M", type=int, default=64, help="Block length M.")
    parser.add_argument("--N", type=int, default=24, help="Number of spectra per block (Stage 1).")
    parser.add_argument("--d", type=float, default=1.0, help="Shape parameter d.")
    parser.add_argument(
        "--pfa",
        type=float,
        default=1e-3,
        help="One-sided probability of false alarm used to compute thresholds.",
    )
    parser.add_argument(
        "--start-idx",
        type=int,
        default=0,
        help="0-based starting time index in raw file.",
    )
    parser.add_argument(
        "--ns-max",
        type=int,
        default=None,
        help="Maximum number of time samples to process (None = to end of file).",
    )

    args = parser.parse_args()

    inputs = _collect_inputs(args.files, args.indir, args.pattern)
    if not inputs:
        parser.error("No input files found. Provide files and/or --indir/--pattern.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    stream_script = os.path.join(script_dir, "ovro_lwa_sk_stream.py")

    os.makedirs(args.outdir, exist_ok=True)
    print(f"[INFO] Output directory for SK stream: {os.path.abspath(args.outdir)}")

    for path in inputs:
        print("=" * 60)
        print(f"[INFO] Processing raw file: {path}")

        cmd = [
            sys.executable,
            stream_script,
            path,
            "--M",
            str(args.M),
            "--N",
            str(args.N),
            "--d",
            str(args.d),
            "--pfa",
            str(args.pfa),
            "--start-idx",
            str(args.start_idx),
            "--out",
            args.outdir,
        ]
        if args.ns_max is not None:
            cmd.extend(["--ns-max", str(args.ns_max)])

        print("[INFO] Command:", " ".join(cmd))
        if args.dry_run:
            print("[DRY-RUN] Not executing.")
            continue

        ret = subprocess.call(cmd)
        if ret != 0:
            print(f"[ERROR] ovro_lwa_sk_stream.py failed for {path} (exit code {ret})")

    print("=" * 60)
    print("[INFO] Batch SK streaming finished.")


if __name__ == "__main__":
    main()
