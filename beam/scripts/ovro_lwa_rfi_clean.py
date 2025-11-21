#!/usr/bin/env python3
"""
ovro_lwa_rfi_clean.py — RFI cleaning of OVRO-LWA SK-stream products.

Input:
    HDF5 file produced by ovro_lwa_sk_stream.py, containing:
        s1_xx           (T, F)      optional
        s1_yy           (T, F)      optional
        sk_flags_xx     (T, F)      optional
        sk_flags_yy     (T, F)      optional
        freq_hz         (F,)
        time_blk        (T,)
    root attributes:
        M, N, d, pfa    (if present)

Processing:
    - Build good/bad masks from SK flags for XX and YY
    - Combine masks according to --flag-mode:
        * 'separate' : XX and YY each use their own flags
        * 'or'       : flagged = flagged_xx OR flagged_yy (shared mask)
        * 'and'      : flagged = flagged_xx AND flagged_yy (shared mask)
    - Integrate in frequency over blocks of size F_block (default 8):
        F_eff    = (F // F_block) * F_block
        n_blocks = F_eff / F_block
      For each polarization and each block:
        - s1_sum    = sum(s1 * good_mask) over channels in block
        - n_good    = sum(good_mask) over channels in block (0..F_block)
        - if n_good > 0:
              avg_good    = s1_sum / n_good
              s1_clean    = avg_good * F_block   (flux-conserving approx)
          else:
              s1_clean    = NaN
    - The "mask" per block is n_good (0..F_block).

Output:
    HDF5 file with datasets:
        s1_xx_clean     (T, n_blocks)    if XX present
        s1_yy_clean     (T, n_blocks)    if YY present
        mask_xx         (T, n_blocks)    n_good per block for XX (or shared)
        mask_yy         (T, n_blocks)    n_good per block for YY (or shared)
        freq_block_hz   (n_blocks,)      block-averaged frequencies
        time_blk        (T,)

    root attributes:
        M, N, d, pfa  (copied from input, if present)
        M_stage1      (alias for M, if present)
        F_block       (int)
        flag_mode     ('separate', 'or', or 'and')
        F_eff         (int)  effective number of channels used
        n_blocks      (int)  number of frequency blocks

Filename:
    By default, output filename is constructed as:
        <base>_rfi_M<M>_F<F_block>_<flag_mode>.h5   (if M known)
        <base>_rfi_F<F_block>_<flag_mode>.h5        (if M missing)
    in the directory given by --out-dir.
"""

from __future__ import annotations

import argparse
import os
from typing import Dict, Any, Tuple

import h5py
import numpy as np


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _build_output_path(
    skfile: str,
    out_dir: str,
    M: int | None,
    F_block: int,
    flag_mode: str,
    suffix: str | None = None,
) -> str:
    """
    Build an informative output filename based on the input SK-stream file
    and RFI-clean parameters.
    """
    base = os.path.splitext(os.path.basename(skfile))[0]

    if suffix is None:
        if M is not None and M >= 0:
            suffix = f"rfi_M{M}_F{F_block}_{flag_mode}"
        else:
            suffix = f"rfi_F{F_block}_{flag_mode}"

    fname = f"{base}_{suffix}.h5"
    return os.path.join(out_dir, fname)


def _load_skstream(skfile: str) -> Dict[str, Any]:
    """
    Load SK-stream product produced by ovro_lwa_sk_stream.py.

    Returns a dict with:
        s1_xx, s1_yy, flags_xx, flags_yy, freq_hz, time_blk,
        has_xx, has_yy, attrs (M, N, d, pfa when present)
    """
    data: Dict[str, Any] = {}
    with h5py.File(skfile, "r") as f:
        # Basic datasets
        if "freq_hz" not in f or "time_blk" not in f:
            raise KeyError("Input file must contain 'freq_hz' and 'time_blk' datasets.")

        freq_hz = np.asarray(f["freq_hz"][:], float)
        time_blk = np.asarray(f["time_blk"][:], float)
        data["freq_hz"] = freq_hz
        data["time_blk"] = time_blk

        has_xx = ("s1_xx" in f) and ("sk_flags_xx" in f)
        has_yy = ("s1_yy" in f) and ("sk_flags_yy" in f)
        data["has_xx"] = has_xx
        data["has_yy"] = has_yy

        if not (has_xx or has_yy):
            raise KeyError(
                "SK-stream file must contain at least one of "
                "('s1_xx' & 'sk_flags_xx') or ('s1_yy' & 'sk_flags_yy')."
            )

        if has_xx:
            data["s1_xx"] = np.asarray(f["s1_xx"][:], float)
            data["flags_xx"] = np.asarray(f["sk_flags_xx"][:], float)
        if has_yy:
            data["s1_yy"] = np.asarray(f["s1_yy"][:], float)
            data["flags_yy"] = np.asarray(f["sk_flags_yy"][:], float)

        # Attributes: M, N, d, pfa if present
        attrs = {}
        for key in ("M", "N", "d", "pfa"):
            if key in f.attrs:
                attrs[key] = f.attrs[key]
        data["attrs"] = attrs

    return data


def _clean_with_good_mask(
    s1: np.ndarray,
    good: np.ndarray,
    F_block: int,
) -> Tuple[np.ndarray, np.ndarray, int, int]:
    """
    Given s1(T, F) and good(T, F) boolean mask (True for good channels),
    perform block-wise integration over frequency in chunks of F_block.

    Returns:
        s1_clean (T, n_blocks),
        mask_block (T, n_blocks) number of good channels per block (0..F_block),
        F_eff (int) effective number of channels used,
        n_blocks (int)
    """
    if s1.shape != good.shape:
        raise ValueError("s1 and good mask must have the same shape.")

    T, F = s1.shape
    if F_block <= 0:
        raise ValueError("F_block must be > 0.")

    n_blocks = F // F_block
    F_eff = n_blocks * F_block
    if n_blocks == 0:
        raise ValueError(
            f"F={F} is smaller than F_block={F_block}; no full blocks can be formed."
        )

    # Restrict to full blocks
    s1_eff = s1[:, :F_eff]
    good_eff = good[:, :F_eff]

    # Convert good to float (1.0 for good, 0.0 for bad)
    good_f = good_eff.astype(float)

    # Apply mask and reshape into blocks
    s1_masked = s1_eff * good_f
    s1_blk = s1_masked.reshape(T, n_blocks, F_block)
    good_blk = good_f.reshape(T, n_blocks, F_block)

    # Sum of good samples and count of good channels per block
    s1_sum = np.sum(s1_blk, axis=2)         # (T, n_blocks)
    n_good = np.sum(good_blk, axis=2)       # (T, n_blocks)

    # Average of good channels; avoid division by zero
    avg_good = np.zeros_like(s1_sum)
    np.divide(
        s1_sum,
        n_good,
        out=avg_good,
        where=(n_good > 0),
    )

    # Flux-conserving approx: inflate average back to F_block channels
    s1_clean = avg_good * float(F_block)

    # Where n_good == 0, set s1_clean to NaN
    s1_clean[n_good == 0] = np.nan

    # mask_block = number of good channels (0..F_block)
    mask_block = n_good

    return s1_clean, mask_block, F_eff, n_blocks


def rfi_clean(
    skfile: str,
    F_block: int = 8,
    flag_mode: str = "separate",
    out_dir: str = ".",
) -> str:
    """
    High-level RFI cleaning driver.

    Parameters
    ----------
    skfile : str
        Path to SK-stream HDF5 file.
    F_block : int
        Frequency block size used for integration (default 8).
    flag_mode : {'separate', 'or', 'and'}
        How to combine polarization flags:
          - 'separate' : XX and YY use their own SK flags
          - 'or'       : flagged_comb = flagged_xx OR flagged_yy
          - 'and'      : flagged_comb = flagged_xx AND flagged_yy
    out_dir : str
        Output directory. The filename is auto-generated.

    Returns
    -------
    out_path : str
        Path to the output HDF5 file.
    """
    print(f"[INFO] RFI cleaning input: {skfile}")
    print(f"[INFO] F_block={F_block}, flag_mode={flag_mode}")

    data = _load_skstream(skfile)
    freq = data["freq_hz"]
    time_blk = data["time_blk"]
    has_xx = data["has_xx"]
    has_yy = data["has_yy"]
    attrs = data["attrs"]

    M_stage1 = int(attrs.get("M", -1)) if "M" in attrs else None

    # Prepare boolean good masks from SK flags
    good_xx = None
    good_yy = None

    if has_xx:
        flags_xx = data["flags_xx"]
        good_xx = (flags_xx == 0)
        print(f"[INFO] XX present: s1_xx shape={data['s1_xx'].shape}")

    if has_yy:
        flags_yy = data["flags_yy"]
        good_yy = (flags_yy == 0)
        print(f"[INFO] YY present: s1_yy shape={data['s1_yy'].shape}")

    # Combine masks according to flag_mode
    flag_mode = flag_mode.lower()
    if flag_mode not in ("separate", "or", "and"):
        raise ValueError("flag_mode must be one of: 'separate', 'or', 'and'.")

    good_comb = None
    if flag_mode in ("or", "and") and has_xx and has_yy:
        # flagged booleans
        fxx = (data["flags_xx"] != 0)
        fyy = (data["flags_yy"] != 0)
        if flag_mode == "or":
            flagged_comb = fxx | fyy
        else:  # 'and'
            flagged_comb = fxx & fyy
        good_comb = ~flagged_comb
        print(f"[INFO] Using shared mask for XX/YY via '{flag_mode}' combination.")

    # Clean XX and YY as available
    s1_xx_clean = mask_xx_block = None
    s1_yy_clean = mask_yy_block = None
    F_eff = n_blocks = None

    if has_xx:
        s1_xx = data["s1_xx"]
        good_for_xx = good_comb if good_comb is not None else good_xx
        s1_xx_clean, mask_xx_block, F_eff_xx, n_blocks_xx = _clean_with_good_mask(
            s1_xx, good_for_xx, F_block
        )
        F_eff = F_eff_xx
        n_blocks = n_blocks_xx

    if has_yy:
        s1_yy = data["s1_yy"]
        good_for_yy = good_comb if good_comb is not None else good_yy
        s1_yy_clean, mask_yy_block, F_eff_yy, n_blocks_yy = _clean_with_good_mask(
            s1_yy, good_for_yy, F_block
        )
        if F_eff is None:
            F_eff = F_eff_yy
            n_blocks = n_blocks_yy
        else:
            if (F_eff != F_eff_yy) or (n_blocks != n_blocks_yy):
                raise RuntimeError(
                    "Inconsistent F_eff or n_blocks between XX and YY cleaning."
                )

    if F_eff is None or n_blocks is None:
        raise RuntimeError("No polarization was cleaned; nothing to write.")

    print(f"[INFO] Effective F_eff={F_eff}, n_blocks={n_blocks}")

    # Build block-averaged frequencies
    freq_eff = freq[:F_eff]
    freq_blk = freq_eff.reshape(n_blocks, F_block).mean(axis=1)

    # Determine output path
    os.makedirs(out_dir, exist_ok=True)
    out_path = _build_output_path(skfile, out_dir, M_stage1, F_block, flag_mode)
    print(f"[INFO] Output file: {out_path}")

    # Write output HDF5
    with h5py.File(out_path, "w") as g:
        # Core datasets
        g.create_dataset("time_blk", data=time_blk, compression="gzip")
        g.create_dataset("freq_block_hz", data=freq_blk, compression="gzip")

        if has_xx and s1_xx_clean is not None and mask_xx_block is not None:
            g.create_dataset("s1_xx_clean", data=s1_xx_clean, compression="gzip")
            g.create_dataset("mask_xx", data=mask_xx_block, compression="gzip")

        if has_yy and s1_yy_clean is not None and mask_yy_block is not None:
            g.create_dataset("s1_yy_clean", data=s1_yy_clean, compression="gzip")
            g.create_dataset("mask_yy", data=mask_yy_block, compression="gzip")

        # Attributes: copy SK parameters, then add RFI-clean metadata
        for key, val in attrs.items():
            g.attrs[key] = val

        if M_stage1 is not None and M_stage1 >= 0:
            g.attrs["M_stage1"] = int(M_stage1)

        g.attrs["F_block"] = int(F_block)
        g.attrs["flag_mode"] = str(flag_mode)
        g.attrs["F_eff"] = int(F_eff)
        g.attrs["n_blocks"] = int(n_blocks)

    print("[INFO] RFI cleaning complete.")
    return out_path


# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "RFI cleaning of OVRO-LWA SK-stream products produced by "
            "ovro_lwa_sk_stream.py."
        )
    )
    ap.add_argument(
        "skfile",
        type=str,
        help="Input SK-stream HDF5 file (e.g. *_skstream.h5).",
    )
    ap.add_argument(
        "--F-block",
        type=int,
        dest="F_block",
        default=8,
        help="Frequency block size for integration (default: 8).",
    )
    ap.add_argument(
        "--flag-mode",
        type=str,
        default="separate",
        choices=["separate", "or", "and"],
        help=(
            "How to combine XX/YY flags: "
            "'separate' (default), 'or', or 'and'."
        ),
    )
    ap.add_argument(
        "--out-dir",
        type=str,
        default=".",
        help="Output directory for the cleaned HDF5 file (default: current directory).",
    )

    args = ap.parse_args()

    if not os.path.exists(args.skfile):
        raise FileNotFoundError(args.skfile)

    rfi_clean(
        skfile=args.skfile,
        F_block=args.F_block,
        flag_mode=args.flag_mode,
        out_dir=args.out_dir,
    )


if __name__ == "__main__":
    main()
