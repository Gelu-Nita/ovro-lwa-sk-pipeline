#!/usr/bin/env python3
"""
ovro_lwa_batch_rfi_clean.py

Batch wrapper around ovro_lwa_rfi_clean.py for many *_skstream.h5 files.
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

    for f in files:
        if os.path.exists(f):
            paths.append(os.path.abspath(f))
        else:
            print(f"[WARN] Input file not found, skipping: {f}")

    if indir is not None:
        indir = os.path.abspath(indir)
        glob_pattern = os.path.join(indir, pattern)
        found = sorted(glob.glob(glob_pattern))
        if not found:
            print(f"[WARN] No files matched pattern '{glob_pattern}'")
        else:
            paths.extend(found)

    seen = set()
    uniq = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    return uniq


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch RFI cleaning (ovro_lwa_rfi_clean.py) for SK-stream products."
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="SK-stream files (*_skstream.h5).",
    )
    parser.add_argument(
        "--indir",
        type=str,
        default=None,
        help="Directory to scan for *_skstream.h5 files.",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*_skstream.h5",
        help="Glob pattern within --indir (default: '*_skstream.h5').",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        required=True,
        help="Output directory for *_skstream_rfi_*.h5 results.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the commands that would be run, but do not execute them.",
    )

    parser.add_argument(
        "--F-block",
        type=int,
        default=8,
        help="Number of adjacent frequency channels per integration block.",
    )
    parser.add_argument(
        "--flag-mode",
        choices=["separate", "or", "and"],
        default="separate",
        help="How to combine XX/YY flags into the mask.",
    )

    args = parser.parse_args()

    inputs = _collect_inputs(args.files, args.indir, args.pattern)
    if not inputs:
        parser.error("No input files found. Provide files and/or --indir/--pattern.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    rfi_script = os.path.join(script_dir, "ovro_lwa_rfi_clean.py")

    os.makedirs(args.outdir, exist_ok=True)
    print(f"[INFO] Output directory for RFI-cleaned products: {os.path.abspath(args.outdir)}")

    for path in inputs:
        print("=" * 60)
        print(f"[INFO] RFI-cleaning SK-stream file: {path}")

        cmd = [
            sys.executable,
            rfi_script,
            path,
            "--F-block",
            str(args.F_block),
            "--flag-mode",
            args.flag_mode,
            "--out",
            args.outdir,
        ]

        print("[INFO] Command:", " ".join(cmd))
        if args.dry_run:
            print("[DRY-RUN] Not executing.")
            continue

        ret = subprocess.call(cmd)
        if ret != 0:
            print(f"[ERROR] ovro_lwa_rfi_clean.py failed for {path} (exit code {ret})")

    print("=" * 60)
    print("[INFO] Batch RFI cleaning finished.")


if __name__ == "__main__":
    main()
