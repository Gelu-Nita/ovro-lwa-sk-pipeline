#!/usr/bin/env python3
"""
ovro_lwa_batch_twostage.py

Batch wrapper for ovro-lwa.py (two-stage SK analysis).

Usage examples
--------------

# Process three files for both polarizations (default) and save plots:
python ovro_lwa_batch_twostage.py \
    /nas8/lwa/event-spectrum/typeI1ms/060963_182827094797b4e9492 \
    /nas8/lwa/event-spectrum/typeI1ms/060963_182221509087db0347f \
    /nas8/lwa/event-spectrum/typeI1ms/060963_1759063729619b7173f \
    --outdir ./results \
    --save-plot --save-npz \
    --scale log log log linear \
    --vmin 1e6 1e6 1e6 1e6 \
    --vmax 1e8 1e8 1e8 1e8 \
    --log-eps 1e-6 1e-6 1e-6 1e-6 \
    --cmap magma \
    --no-context \
    --no-show

# Process only XX for all files:
python ovro_lwa_batch_twostage.py files*.h5 --pol XX --outdir ./results --save-plot

Notes
-----
- All arguments *other than* `files`, `--pol`, and `--outdir` are passed
  straight through to ovro-lwa.py, unchanged.
- Per-panel arguments like
    --scale log log log linear
  are therefore supported exactly as ovro-lwa.py expects.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import subprocess
from typing import List


def _expand_inputs(patterns: List[str]) -> List[str]:
    """
    Expand a list of filenames or glob patterns into a unique ordered list.
    If a pattern matches nothing, it is kept as-is (ovro-lwa.py will then
    apply its own .h5/.hdf5 resolution).
    """
    out: List[str] = []
    for p in patterns:
        matches = glob.glob(p)
        if matches:
            matches = sorted(matches)
            out.extend(matches)
        else:
            out.append(p)

    # Deduplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for f in out:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Batch wrapper for ovro-lwa.py (two-stage SK analysis).\n\n"
            "All unknown options are forwarded verbatim to ovro-lwa.py, "
            "so you can use exactly the same CLI options as in single-file mode."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Input OVRO-LWA HDF5 files or glob patterns.",
    )
    parser.add_argument(
        "--pol",
        choices=["XX", "YY", "both"],
        default="both",
        help=(
            "Which polarization(s) to process. "
            "'both' runs ovro-lwa.py twice (XX and YY). Default: both."
        ),
    )
    parser.add_argument(
        "--outdir",
        default=".",
        help=(
            "Output directory passed to ovro-lwa.py as --outdir. "
            "Defaults to current directory."
        ),
    )

    # Everything else is passed through unchanged to ovro-lwa.py
    args, passthrough = parser.parse_known_args()

    files = _expand_inputs(args.files)
    if not files:
        print("[WARN] No input files found; nothing to do.")
        return

    # Locate ovro-lwa.py in the same directory as this script
    here = os.path.dirname(os.path.abspath(__file__))
    ovro_script = os.path.join(here, "ovro-lwa.py")
    if not os.path.exists(ovro_script):
        print(f"[ERROR] Could not find 'ovro-lwa.py' next to {__file__}")
        sys.exit(1)

    # Decide polarizations to run
    if args.pol == "both":
        pol_list = ["XX", "YY"]
    else:
        pol_list = [args.pol]

    print("============================================================")
    print("[INFO] ovro_lwa_batch_twostage.py starting")
    print(f"[INFO] Using ovro-lwa.py at: {ovro_script}")
    print(f"[INFO] Output base directory (ovro-lwa --outdir): {os.path.abspath(args.outdir)}")
    print(f"[INFO] Extra arguments passed through to ovro-lwa.py: {' '.join(passthrough) or '(none)'}")
    print("============================================================")

    for h5 in files:
        print("------------------------------------------------------------")
        print(f"[INFO] Processing input: {h5}")
        for pol in pol_list:
            cmd = [
                sys.executable,
                ovro_script,
                h5,
                "--pol",
                pol,
                "--outdir",
                args.outdir,
            ]
            cmd.extend(passthrough)

            print(f"[INFO]   Running ovro-lwa.py for pol={pol}")
            print(f"[INFO]   Command: {' '.join(cmd)}")

            result = subprocess.run(cmd)
            if result.returncode != 0:
                print(
                    f"[WARN] ovro-lwa.py exited with code {result.returncode} "
                    f"for file={h5}, pol={pol}"
                )
            else:
                print(f"[INFO]   Completed successfully for pol={pol}")

    print("============================================================")
    print("[INFO] Batch two-stage processing complete.")


if __name__ == "__main__":
    main()
