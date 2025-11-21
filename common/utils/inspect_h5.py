#!/usr/bin/env python3
"""
inspect_h5.py — dump the structure of an HDF5 file (groups, datasets, shapes, dtypes, size, attrs).

Usage examples:

  python inspect_h5.py myfile.h5

  python inspect_h5.py myfile.h5 --show-attrs

  python inspect_h5.py myfile.h5 --show-attrs --max-attr-len 120
"""

from __future__ import annotations

import argparse
import os
from typing import Any

import h5py
import numpy as np


def _short_repr(val: Any, max_len: int = 80) -> str:
    """Compact repr for attribute values, with truncation for long strings/arrays."""
    if isinstance(val, bytes):
        s = val.decode("utf-8", errors="replace")
    else:
        s = repr(val)

    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return s


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Inspect the structure of an HDF5 file (groups, datasets, shapes, dtypes, size, attrs)."
    )
    ap.add_argument("h5file", help="Path to the HDF5 file to inspect.")
    ap.add_argument(
        "--show-attrs",
        action="store_true",
        help="Also list attributes for each group/dataset.",
    )
    ap.add_argument(
        "--max-attr-len",
        type=int,
        default=80,
        help="Maximum length of printed attribute values (default: 80).",
    )
    args = ap.parse_args()

    path = args.h5file
    if not os.path.exists(path):
        raise FileNotFoundError(f"HDF5 file not found: {path}")

    print(f"========================================")
    print(f"HDF5 file: {os.path.abspath(path)}")
    print(f"========================================")

    with h5py.File(path, "r") as f:
        # Basic file-level attrs
        if args.show_attrs and f.attrs:
            print("[FILE ATTRS]")
            for k, v in f.attrs.items():
                print(f"  @{k} = {_short_repr(v, args.max_attr_len)}")
            print()

        def _visit(name: str, obj: h5py.Dataset | h5py.Group) -> None:
            indent = "  "
            if isinstance(obj, h5py.Group):
                print(f"[GROUP]   /{name}")
            elif isinstance(obj, h5py.Dataset):
                # Approx size in MiB
                n_elem = int(np.prod(obj.shape)) if obj.shape else 1
                bytes_total = n_elem * obj.dtype.itemsize
                mib = bytes_total / (1024.0 * 1024.0)
                print(
                    f"[DATASET] /{name}  "
                    f"shape={obj.shape}  dtype={obj.dtype}  ~{mib:.2f} MiB"
                )
            else:
                # Should not happen in normal h5py usage
                print(f"[UNKNOWN] /{name}  type={type(obj)}")

            if args.show_attrs and obj.attrs:
                for k, v in obj.attrs.items():
                    print(f"{indent}@{k} = {_short_repr(v, args.max_attr_len)}")

        # Root group
        print("[ROOT GROUP] /")
        f.visititems(_visit)


if __name__ == "__main__":
    main()
