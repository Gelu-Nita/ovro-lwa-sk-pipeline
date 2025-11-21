#!/usr/bin/env python3
"""
ovro_lwa_batch_quicklook.py

Batch wrapper around ovro_lwa_sk_quicklook.py to generate and save PNG quicklook plots.
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
        description="Batch quicklook PNG generation (ovro_lwa_sk_quicklook.py)."
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Input SK-stream or RFI-cleaned files (*.h5).",
    )
    parser.add_argument(
        "--indir",
        type=str,
        default=None,
        help="Directory to scan for input files (*.h5).",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.h5",
        help="Glob pattern within --indir (default: '*.h5').",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        required=True,
        help="Output directory for PNG quicklook plots.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the commands that would be run, but do not execute them.",
    )

    # Plot options mirrored from ovro_lwa_sk_quicklook.py
    parser.add_argument(
        "--pol",
        choices=["XX", "YY", "both"],
        default="both",
        help="Polarization selector passed to quicklook (default: both).",
    )
    parser.add_argument(
        "--scale",
        choices=["linear", "log"],
        default="linear",
        help="Scaling for S1 panels.",
    )
    parser.add_argument(
        "--vmin",
        type=float,
        default=None,
        help="vmin for S1 panels.",
    )
    parser.add_argument(
        "--vmax",
        type=float,
        default=None,
        help="vmax for S1 panels.",
    )
    parser.add_argument(
        "--log-eps",
        type=float,
        default=None,
        help="Floor value for log scaling.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG dpi.",
    )
    parser.add_argument(
        "--transparent",
        action="store_true",
        help="Save PNGs with transparent background.",
    )

    args = parser.parse_args()

    inputs = _collect_inputs(args.files, args.indir, args.pattern)
    if not inputs:
        parser.error("No input files found. Provide files and/or --indir/--pattern.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ql_script = os.path.join(script_dir, "ovro_lwa_sk_quicklook.py")

    os.makedirs(args.outdir, exist_ok=True)
    print(f"[INFO] Output directory for PNG quicklooks: {os.path.abspath(args.outdir)}")

    for path in inputs:
        print("=" * 60)
        print(f"[INFO] Quicklook for file: {path}")

        cmd = [
            sys.executable,
            ql_script,
            path,
            "--pol",
            args.pol,
            "--scale",
            args.scale,
            "--save-plot",
            "png",
            "--out",
            args.outdir,
            "--dpi",
            str(args.dpi),
            "--no-show",
        ]
        if args.vmin is not None:
            cmd.extend(["--vmin", str(args.vmin)])
        if args.vmax is not None:
            cmd.extend(["--vmax", str(args.vmax)])
        if args.log_eps is not None:
            cmd.extend(["--log-eps", str(args.log_eps)])
        if args.transparent:
            cmd.append("--transparent")

        print("[INFO] Command:", " ".join(cmd))
        if args.dry_run:
            print("[DRY-RUN] Not executing.")
            continue

        ret = subprocess.call(cmd)
        if ret != 0:
            print(f"[ERROR] ovro_lwa_sk_quicklook.py failed for {path} (exit code {ret})")

    print("=" * 60)
    print("[INFO] Batch quicklook generation finished.")


if __name__ == "__main__":
    main()
