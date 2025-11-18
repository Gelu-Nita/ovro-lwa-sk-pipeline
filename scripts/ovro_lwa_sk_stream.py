#!/usr/bin/env python3
"""
ovro_lwa_sk_stream.py

Streaming SK "spectrometer" for OVRO-LWA HDF5 data.

This script reads an OVRO-LWA HDF5 file in non-overlapping blocks of M
spectra and, for EACH BLOCK, computes for BOTH polarizations (XX, YY):

    s1_xx_block(f) = sum_{i=0..M-1} P_xx(i, f)
    s2_xx_block(f) = sum_{i=0..M-1} P_xx(i, f)^2
    sk_xx_block(f) = SK(s1_xx_block, s2_xx_block; M, N, d)

    s1_yy_block(f) = sum_{i=0..M-1} P_yy(i, f)
    s2_yy_block(f) = sum_{i=0..M-1} P_yy(i, f)^2
    sk_yy_block(f) = SK(s1_yy_block, s2_yy_block; M, N, d)

Flags are then computed independently for each polarization:

    sk_flags_xx(f) = -1, 0, +1
    sk_flags_yy(f) = -1, 0, +1

based on SK thresholds for the given (M, N, d, pfa).

Output HDF5 file contains datasets:

    - "s1_xx"       : (T, F) float32
    - "s1_yy"       : (T, F) float32
    - "sk_flags_xx" : (T, F) int8   (flags from XX SK)
    - "sk_flags_yy" : (T, F) int8   (flags from YY SK)
    - "freq_hz"     : (F,)   float64
    - "time_blk"    : (T,)   float64  (block-center times derived from input)

and file-level attributes:

    - "M", "N", "d", "pfa"
    - "ns_total", "ns_start", "ns_eff", "nfreq"
    - a description string.

A tqdm progress bar is used if available; otherwise, the script falls back
to occasional text progress messages.
"""

from __future__ import annotations

import argparse
import os
from typing import Optional, Tuple

import numpy as np
import h5py

import pygsk.core as core
from pygsk.thresholds import compute_sk_thresholds

# Optional tqdm for progress bar
try:
    from tqdm import tqdm  # type: ignore
except Exception:  # ImportError or anything else weird
    tqdm = None


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _load_time_array(ds_time: h5py.Dataset, ns_total: int) -> np.ndarray:
    """
    Load time dataset as a 1-D float array (seconds since epoch, or numeric),
    handling both numeric and ISO-string representations.
    """
    t = ds_time[:]
    if t.ndim != 1 or t.shape[0] != ns_total:
        raise ValueError(
            f"'time' dataset must be 1-D with length {ns_total}, got shape {t.shape}"
        )

    if np.issubdtype(t.dtype, np.number):
        return np.asarray(t, dtype=float)

    # Assume string-like; parse ISO timestamps to UNIX seconds
    t_str = np.array(t, dtype=str)

    from datetime import datetime, timezone

    def _parse_iso_to_unix(s: str) -> float:
        # Handle trailing 'Z' as UTC
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.timestamp()

    return np.array([_parse_iso_to_unix(s) for s in t_str], dtype=float)


def _open_datasets(
    h5_path: str,
) -> Tuple[h5py.File, h5py.Dataset, h5py.Dataset, np.ndarray, np.ndarray]:
    """
    Open OVRO-LWA HDF5 file and return:

        fin     : open h5py.File (caller must close)
        ds_xx   : dataset for XX power, shape (ns, nf)
        ds_yy   : dataset for YY power, shape (ns, nf)
        freq    : (nf,) float64 array in Hz
        time    : (ns,) float64 array (seconds since epoch, or numeric)

    If the 'time' dataset is missing, a synthetic time axis equal to
    np.arange(ns, dtype=float) is used.
    """
    fin = h5py.File(h5_path, "r")
    group = "Observation1/Tuning1"

    ds_xx = fin[f"{group}/XX"]
    ds_yy = fin[f"{group}/YY"]
    ds_freq = fin[f"{group}/freq"]

    ns_total_xx, nf_xx = ds_xx.shape
    ns_total_yy, nf_yy = ds_yy.shape
    if ns_total_xx != ns_total_yy or nf_xx != nf_yy:
        fin.close()
        raise ValueError(
            f"XX and YY shapes mismatch: XX={ds_xx.shape}, YY={ds_yy.shape}"
        )

    ns_total = ns_total_xx
    nf = nf_xx

    freq = np.asarray(ds_freq[:], dtype=float)
    if freq.shape[0] != nf:
        fin.close()
        raise ValueError(
            f"Frequency axis length {freq.shape[0]} does not match data nfreq={nf}."
        )

    # Time (expected for time_blk) – but tolerate missing dataset
    time_path = f"{group}/time"
    if time_path in fin:
        ds_time = fin[time_path]
        time = _load_time_array(ds_time, ns_total=ns_total)
    else:
        print(
            f"[WARN] Dataset '{time_path}' not found in {h5_path}; "
            "using synthetic time axis (0, 1, 2, ...)."
        )
        time = np.arange(ns_total, dtype=float)

    return fin, ds_xx, ds_yy, freq, time



# ----------------------------------------------------------------------
# Main streaming SK pipeline
# ----------------------------------------------------------------------
def stream_sk_dualpol(
    h5_path: str,
    out_path: str,
    *,
    M: int = 64,
    N: int = 24,
    d: float = 1.0,
    pfa: float = 1e-3,
    start_idx: int = 0,
    ns_max: Optional[int] = None,
    compression: str = "gzip",
) -> None:
    """
    Streaming SK "spectrometer" pipeline for BOTH polarizations (XX and YY).

    For each non-overlapping block of M spectra, compute:

        s1_xx_block, s2_xx_block, sk_xx_block, sk_flags_xx
        s1_yy_block, s2_yy_block, sk_yy_block, sk_flags_yy

    using the same (M, N, d, pfa) for both pols.

    Parameters
    ----------
    h5_path : str
        Input OVRO-LWA HDF5 file (single tuning; must contain XX, YY, freq, time).
    out_path : str
        Output HDF5 file to write (will be overwritten if exists).
    M : int
        Number of spectra per non-overlapping SK block (default: 64).
    N : int
        Gamma shape parameter N used in SK theory (default: 24).
    d : float
        Gamma scale parameter d (default: 1.0).
    pfa : float
        One-sided probability of false alarm used to set SK thresholds (default: 1e-3).
    start_idx : int
        0-based starting index in time to process (default: 0).
    ns_max : int or None
        Optional maximum number of time samples to process after start_idx.
        If None, process until end of dataset.
    compression : str
        HDF5 compression filter for s1_xx/s1_yy/sk_flags_* datasets
        (e.g. 'gzip', 'lzf', or None to disable).
    """
    print(f"[INFO] Input HDF5: {h5_path}")
    print(f"[INFO] SK parameters: M={M}, N={N}, d={d}, pfa={pfa}")

    fin, ds_xx, ds_yy, freq, time = _open_datasets(h5_path)
    ns_total, nf = ds_xx.shape
    print(f"[INFO] Raw shape: ns={ns_total}, nf={nf}")

    if start_idx < 0 or start_idx >= ns_total:
        fin.close()
        raise ValueError(
            f"start_idx={start_idx} is out of range for ns_total={ns_total}."
        )

    # Determine selection length
    if ns_max is None:
        ns_sel = ns_total - start_idx
    else:
        if ns_max <= 0:
            fin.close()
            raise ValueError("ns_max must be a positive integer if provided.")
        ns_sel = min(ns_max, ns_total - start_idx)

    if ns_sel <= 0:
        fin.close()
        raise ValueError(
            f"No samples selected: start_idx={start_idx}, ns_max={ns_max}, ns_total={ns_total}."
        )

    # Number of full blocks
    T = ns_sel // M
    ns_eff = T * M
    if T <= 0:
        fin.close()
        raise ValueError(
            f"Not enough samples ({ns_sel}) to form even one block of size M={M}."
        )

    if ns_eff != ns_sel:
        print(
            f"[WARN] ns_sel={ns_sel} is not a multiple of M={M}; "
            f"using only ns_eff={ns_eff} samples (dropping tail of length {ns_sel - ns_eff})."
        )

    print(f"[INFO] Effective samples: ns_eff={ns_eff} → T={T} blocks of size M={M}.")

    # SK thresholds (same for both pols)
    lower, upper, _ = compute_sk_thresholds(M, N=N, d=d, pfa=pfa)
    print(f"[INFO] SK thresholds: lower={lower:.6g}, upper={upper:.6g}")

    # Prepare output file
    if os.path.exists(out_path):
        print(f"[WARN] Overwriting existing output file: {out_path}")
        os.remove(out_path)

    fout = h5py.File(out_path, "w")

    # Datasets: S1 for both pols, flags for both, freq and time_blk
    dset_s1_xx = fout.create_dataset(
        "s1_xx",
        shape=(T, nf),
        dtype="float32",
        chunks=(1, nf),
        compression=compression,
        shuffle=True if compression is not None else False,
    )

    dset_s1_yy = fout.create_dataset(
        "s1_yy",
        shape=(T, nf),
        dtype="float32",
        chunks=(1, nf),
        compression=compression,
        shuffle=True if compression is not None else False,
    )

    dset_flags_xx = fout.create_dataset(
        "sk_flags_xx",
        shape=(T, nf),
        dtype="int8",
        chunks=(1, nf),
        compression=compression,
        shuffle=True if compression is not None else False,
    )

    dset_flags_yy = fout.create_dataset(
        "sk_flags_yy",
        shape=(T, nf),
        dtype="int8",
        chunks=(1, nf),
        compression=compression,
        shuffle=True if compression is not None else False,
    )

    dset_freq = fout.create_dataset(
        "freq_hz",
        data=freq.astype("float64"),
        dtype="float64",
    )

    dset_time_blk = fout.create_dataset(
        "time_blk",
        shape=(T,),
        dtype="float64",
    )

    # File-level metadata
    fout.attrs["input_file"] = os.path.abspath(h5_path)
    fout.attrs["M"] = int(M)
    fout.attrs["N"] = int(N)
    fout.attrs["d"] = float(d)
    fout.attrs["pfa"] = float(pfa)
    fout.attrs["ns_total"] = int(ns_total)
    fout.attrs["ns_start"] = int(start_idx)
    fout.attrs["ns_eff"] = int(ns_eff)
    fout.attrs["nfreq"] = int(nf)
    fout.attrs["description"] = (
        "Streaming SK spectrometer product: s1_xx(t,f), s1_yy(t,f), "
        "and SK flags for XX and YY (sk_flags_xx, sk_flags_yy) computed "
        "from non-overlapping blocks of M spectra. "
        "time_blk is the block-center time derived from the original time array."
    )

    print("[INFO] Starting streaming SK computation (XX and YY, flags for both)...")

    # Choose iterator with or without tqdm
    if tqdm is not None:
        iterator = tqdm(range(T), desc="SK blocks", unit="block")
    else:
        iterator = range(T)

    # Iterate over blocks
    for k in iterator:
        i0 = start_idx + k * M
        i1 = i0 + M

        # Read blocks (M, nf) for XX and YY as float64 for numerics
        block_xx = np.asarray(ds_xx[i0:i1, :], dtype=np.float64)
        block_yy = np.asarray(ds_yy[i0:i1, :], dtype=np.float64)

        # Time block (we take its mean as block center)
        t_block = time[i0:i1]
        time_blk_k = float(np.mean(t_block))
        dset_time_blk[k] = time_blk_k

        # S1 for both pols
        s1_xx_block = block_xx.sum(axis=0, dtype=np.float64)  # (nf,)
        s1_yy_block = block_yy.sum(axis=0, dtype=np.float64)  # (nf,)

        # S2 for both pols
        s2_xx_block = np.square(block_xx, dtype=np.float64).sum(axis=0)  # (nf,)
        s2_yy_block = np.square(block_yy, dtype=np.float64).sum(axis=0)  # (nf,)

        # Compute SK for XX and YY; core.get_sk expects 2-D input
        sk_xx_block = core.get_sk(
            s1_xx_block[None, :],
            s2_xx_block[None, :],
            M=M,
            N=N,
            d=d,
        )[0, :]  # (nf,)

        sk_yy_block = core.get_sk(
            s1_yy_block[None, :],
            s2_yy_block[None, :],
            M=M,
            N=N,
            d=d,
        )[0, :]  # (nf,)

        # Flags from SK for both pols
        flags_xx = np.zeros_like(sk_xx_block, dtype=np.int8)
        flags_yy = np.zeros_like(sk_yy_block, dtype=np.int8)

        flags_xx[sk_xx_block < lower] = -1
        flags_xx[sk_xx_block > upper] = +1

        flags_yy[sk_yy_block < lower] = -1
        flags_yy[sk_yy_block > upper] = +1

        # Store results (S1 as float32, flags as int8)
        dset_s1_xx[k, :] = s1_xx_block.astype("float32")
        dset_s1_yy[k, :] = s1_yy_block.astype("float32")
        dset_flags_xx[k, :] = flags_xx
        dset_flags_yy[k, :] = flags_yy

        # If tqdm is not available, print occasional progress
        if tqdm is None:
            if (k + 1) % 100 == 0 or (k + 1) == T:
                print(f"[INFO] Processed block {k+1}/{T}")

    print(f"[INFO] Finished streaming SK computation for {T} blocks.")

    fout.close()
    fin.close()

    print(f"[INFO] Output written to: {out_path}")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Streaming SK spectrometer for OVRO-LWA: "
            "compute block-integrated s1_xx, s1_yy and independent SK flags "
            "for XX and YY, saving a reduced HDF5 product."
        )
    )

    ap.add_argument(
        "h5file",
        type=str,
        help="Input OVRO-LWA HDF5 file (single tuning). "
             "You can omit the .h5/.hdf5 extension; common suffixes are tried."
    )
    ap.add_argument(
        "-o", "--out",
        type=str,
        default=None,
        help=(
            "Output HDF5 file. "
            "If omitted, defaults to <basename>_skstream.h5 in the current directory. "
            "If this is an existing directory, the default filename is placed inside "
            "that directory."
        ),
    )

    ap.add_argument("--M", type=int, default=64,
                    help="Number of spectra per SK block (default: 64).")
    ap.add_argument("--N", type=int, default=24,
                    help="Gamma shape parameter N used in SK (default: 24).")
    ap.add_argument("--d", type=float, default=1.0,
                    help="Gamma scale parameter d used in SK (default: 1.0).")
    ap.add_argument("--pfa", type=float, default=1e-3,
                    help="One-sided probability of false alarm (default: 1e-3).")

    ap.add_argument("--start-idx", type=int, default=0,
                    help="0-based starting time index to read (default: 0).")
    ap.add_argument("--ns-max", type=int, default=None,
                    help="Optional maximum number of time samples to process (default: all).")

    ap.add_argument(
        "--no-compression",
        action="store_true",
        help="Disable HDF5 compression for s1_xx/s1_yy/sk_flags_* datasets.",
    )

    args = ap.parse_args()

    # Resolve input HDF5 path (allow bare basename without extension)
    h5_path = args.h5file
    if not os.path.exists(h5_path):
        candidates = [f"{h5_path}.h5", f"{h5_path}.hdf5"]
        existing = [c for c in candidates if os.path.exists(c)]
        if existing:
            h5_path = existing[0]
            print(f"[INFO] Input file not found exactly, using candidate: {h5_path}")
        else:
            raise FileNotFoundError(
                f"Could not find HDF5 file at '{args.h5file}' or any of {candidates}"
            )

    base = os.path.splitext(os.path.basename(h5_path))[0]

    # Resolve output path:
    #   - if out is None            -> ./<basename>_skstream.h5
    #   - if out is an existing dir -> <out>/<basename>_skstream.h5
    #   - else                      -> treat out as a file path
    if args.out is None:
        out_path = f"{base}_skstream.h5"
    else:
        out_candidate = args.out
        if os.path.isdir(out_candidate):
            out_path = os.path.join(out_candidate, f"{base}_skstream.h5")
        else:
            out_path = out_candidate

    compression = None if args.no_compression else "gzip"

    stream_sk_dualpol(
        h5_path=h5_path,
        out_path=out_path,
        M=args.M,
        N=args.N,
        d=args.d,
        pfa=args.pfa,
        start_idx=args.start_idx,
        ns_max=args.ns_max,
        compression=compression,
    )



if __name__ == "__main__":
    main()
