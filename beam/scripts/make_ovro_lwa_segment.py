#!/usr/bin/env python3
"""
make_ovro_lwa_demo_segment.py

Create a smaller OVRO–LWA HDF5 file for demos by trimming both
the time and frequency dimensions, while preserving the internal
layout and dtypes of the original file.

It assumes the structure:

  /Observation1/Tuning1/XX       (ntime, nfreq)
  /Observation1/Tuning1/YY       (ntime, nfreq)
  /Observation1/Tuning1/XY_real  (ntime, nfreq)   [optional]
  /Observation1/Tuning1/XY_imag  (ntime, nfreq)   [optional]
  /Observation1/Tuning1/freq     (nfreq,)
  /Observation1/time             (ntime,)

Example:

  python make_ovro_lwa_demo_segment.py \
      input.h5 \
      --n-frames 256 \
      --n-channels 256

Default output file (if --out is omitted):

  <input_basename>_demo.h5

You can also use --t0 / --f0 as aliases for the starting time/frequency indices.
"""

from __future__ import annotations

import argparse
import os
from typing import Optional

import h5py
import numpy as np


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _copy_attrs(src, dst) -> None:
    """Copy all attributes from src object to dst object."""
    for k, v in src.attrs.items():
        dst.attrs[k] = v


def _infer_output_path(in_path: str) -> str:
    """
    Default output path: <base>_demo.h5 in same directory
    (no T/F info, so you can overwrite it for different sizes).
    """
    directory = os.path.dirname(in_path)
    base = os.path.basename(in_path)
    if base.lower().endswith((".h5", ".hdf5")):
        stem = base.rsplit(".", 1)[0]
    else:
        stem = base
    out_name = f"{stem}_demo.h5"
    return os.path.join(directory, out_name)


# ---------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------
def make_demo_segment(
    in_path: str,
    out_path: Optional[str] = None,
    start_idx_time: int = 0,
    n_frames: int = 256,
    start_idx_freq: int = 0,
    n_channels: int = 256,
) -> str:
    """
    Create a trimmed OVRO–LWA HDF5 demo file.

    Returns the output path.
    """
    # Resolve input path: allow bare basename (no extension)
    if not os.path.exists(in_path):
        candidates = [f"{in_path}.h5", f"{in_path}.hdf5"]
        existing = [c for c in candidates if os.path.exists(c)]
        if not existing:
            raise FileNotFoundError(
                f"Could not find input file at '{in_path}' or any of {candidates}"
            )
        in_path = existing[0]

    with h5py.File(in_path, "r") as fin:
        # Check expected datasets
        g_obs = fin.get("Observation1")
        if g_obs is None or not isinstance(g_obs, h5py.Group):
            raise KeyError("Group '/Observation1' not found")

        g_tun = g_obs.get("Tuning1")
        if g_tun is None or not isinstance(g_tun, h5py.Group):
            raise KeyError("Group '/Observation1/Tuning1' not found")

        ds_xx = g_tun["XX"]
        ds_yy = g_tun["YY"]
        ntime, nfreq = ds_xx.shape

        # Optional datasets
        ds_xy_real = g_tun.get("XY_real", None)
        ds_xy_imag = g_tun.get("XY_imag", None)

        ds_freq = g_tun["freq"]

        ds_time = g_obs.get("time", None)
        if ds_time is None:
            raise KeyError("Dataset '/Observation1/time' not found")

        # Validate time slice
        if start_idx_time < 0 or start_idx_time >= ntime:
            raise ValueError(
                f"start-idx-time={start_idx_time} out of range for ntime={ntime}"
            )

        if n_frames <= 0:
            raise ValueError("--n-frames must be > 0")

        T = min(n_frames, ntime - start_idx_time)
        if T <= 0:
            raise ValueError(
                f"No frames selected: start-idx-time={start_idx_time}, "
                f"n_frames={n_frames}, ntime={ntime}"
            )

        time_slice = slice(start_idx_time, start_idx_time + T)

        # Validate freq slice
        if start_idx_freq < 0 or start_idx_freq >= nfreq:
            raise ValueError(
                f"start-idx-freq={start_idx_freq} out of range for nfreq={nfreq}"
            )

        if n_channels <= 0:
            raise ValueError("--n-channels must be > 0")

        F = min(n_channels, nfreq - start_idx_freq)
        if F <= 0:
            raise ValueError(
                f"No channels selected: start-idx-freq={start_idx_freq}, "
                f"n_channels={n_channels}, nfreq={nfreq}"
            )

        freq_slice = slice(start_idx_freq, start_idx_freq + F)

        print("========================================")
        print(f"[INFO] Input file        : {in_path}")
        print(f"[INFO] Full shape XX     : (ntime={ntime}, nfreq={nfreq})")
        print(f"[INFO] Time slice        : [{start_idx_time}:{start_idx_time + T}) → T={T}")
        print(f"[INFO] Freq slice        : [{start_idx_freq}:{start_idx_freq + F}) → F={F}")

        # Decide output path
        if out_path is None:
            out_path = _infer_output_path(in_path)

        # Create output file
        if os.path.exists(out_path):
            print(f"[WARN] Overwriting existing file: {out_path}")

        with h5py.File(out_path, "w") as fout:
            # Copy root attributes, then add demo metadata
            _copy_attrs(fin, fout)
            fout.attrs["demo_source_file"] = os.path.abspath(in_path)
            fout.attrs["demo_t0_index"] = int(start_idx_time)
            fout.attrs["demo_n_frames"] = int(T)
            fout.attrs["demo_f0_index"] = int(start_idx_freq)
            fout.attrs["demo_n_channels"] = int(F)

            # Create /Observation1
            g_obs_out = fout.create_group("Observation1")
            _copy_attrs(g_obs, g_obs_out)

            # Create /Observation1/Tuning1
            g_tun_out = g_obs_out.create_group("Tuning1")
            _copy_attrs(g_tun, g_tun_out)

            # --- Write sliced XX, YY ---
            print("[INFO] Writing XX/YY slices...")
            g_tun_out.create_dataset(
                "XX",
                data=ds_xx[time_slice, freq_slice],
                compression="gzip",
                shuffle=True,
                fletcher32=True,
            )
            _copy_attrs(ds_xx, g_tun_out["XX"])

            g_tun_out.create_dataset(
                "YY",
                data=ds_yy[time_slice, freq_slice],
                compression="gzip",
                shuffle=True,
                fletcher32=True,
            )
            _copy_attrs(ds_yy, g_tun_out["YY"])

            # --- Optional XY_real / XY_imag ---
            if ds_xy_real is not None:
                print("[INFO] Writing XY_real slice...")
                g_tun_out.create_dataset(
                    "XY_real",
                    data=ds_xy_real[time_slice, freq_slice],
                    compression="gzip",
                    shuffle=True,
                    fletcher32=True,
                )
                _copy_attrs(ds_xy_real, g_tun_out["XY_real"])

            if ds_xy_imag is not None:
                print("[INFO] Writing XY_imag slice...")
                g_tun_out.create_dataset(
                    "XY_imag",
                    data=ds_xy_imag[time_slice, freq_slice],
                    compression="gzip",
                    shuffle=True,
                    fletcher32=True,
                )
                _copy_attrs(ds_xy_imag, g_tun_out["XY_imag"])

            # --- Freq subset ---
            print("[INFO] Writing freq slice...")
            g_tun_out.create_dataset(
                "freq",
                data=ds_freq[freq_slice],
                compression="gzip",
                shuffle=True,
                fletcher32=True,
            )
            _copy_attrs(ds_freq, g_tun_out["freq"])

            # --- Time subset (/Observation1/time) ---
            print("[INFO] Writing time slice...")
            g_obs_out.create_dataset(
                "time",
                data=ds_time[time_slice],
                compression="gzip",
                shuffle=True,
                fletcher32=True,
            )
            _copy_attrs(ds_time, g_obs_out["time"])

        # After closing fout, we can check file size
        size_bytes = os.path.getsize(out_path)
        size_mb = size_bytes / (1024.0**2)

        print("========================================")
        print(f"[INFO] Output file       : {out_path}")
        print(f"[INFO] Output shape XX   : (ntime={T}, nfreq={F})")
        print(f"[INFO] Approx file size  : {size_mb:.2f} MiB")
        print(f"[INFO] demo_t0_index     : {start_idx_time}")
        print(f"[INFO] demo_f0_index     : {start_idx_freq}")
        print("========================================")

    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Create a trimmed OVRO–LWA HDF5 demo file by slicing time and frequency."
    )
    ap.add_argument("input", help="Path to the full-size OVRO–LWA HDF5 file (or basename).")
    ap.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output HDF5 path. If omitted, <base>_demo.h5 is used.",
    )

    # Time selection: --start-idx-time, plus alias --t0
    ap.add_argument(
        "--start-idx-time",
        type=int,
        default=0,
        help="Starting time index (0-based) for slicing (default: 0).",
    )
    ap.add_argument(
        "--t0",
        type=int,
        default=None,
        help="Alias for --start-idx-time (starting time index).",
    )
    ap.add_argument(
        "--n-frames",
        type=int,
        default=256,
        help="Number of time frames to keep (default: 256).",
    )

    # Frequency selection: --start-idx-freq, plus alias --f0
    ap.add_argument(
        "--start-idx-freq",
        type=int,
        default=0,
        help="Starting frequency index (0-based) for slicing (default: 0).",
    )
    ap.add_argument(
        "--f0",
        type=int,
        default=None,
        help="Alias for --start-idx-freq (starting frequency index).",
    )
    ap.add_argument(
        "--n-channels",
        type=int,
        default=256,
        help="Number of frequency channels to keep (default: 256).",
    )

    args = ap.parse_args()

    # Use aliases if provided
    start_idx_time = args.t0 if args.t0 is not None else args.start_idx_time
    start_idx_freq = args.f0 if args.f0 is not None else args.start_idx_freq

    make_demo_segment(
        in_path=args.input,
        out_path=args.out,
        start_idx_time=start_idx_time,
        n_frames=args.n_frames,
        start_idx_freq=start_idx_freq,
        n_channels=args.n_channels,
    )


if __name__ == "__main__":
    main()
