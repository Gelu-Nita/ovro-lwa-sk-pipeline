#!/usr/bin/env python3
"""
ovro_lwa_quicklook.py — Unified quicklook for OVRO-LWA SK-stream and RFI-cleaned data.

This tool inspects the HDF5 file and automatically determines:
    • SK-stream product (from ovro_lwa_sk_stream.py)
    • RFI-cleaned product (from ovro_lwa_rfi_clean.py)

Then it produces the appropriate quicklook figure.

Layouts:
---------------------------------------------------------------------
SK-stream:
   2×2  (both pols)     Top: S1_xx, S1_yy
                        Bot: flags_xx, flags_yy
   2×1  (single pol)

RFI-cleaned:
   2×2  (both pols)     Top: s1_xx_clean, s1_yy_clean
                        Bot: mask_xx, mask_yy
   2×1  (single pol)

CLI mirrors the existing quicklook:
    --scale log
    --vmin 1e6
    --vmax 1e7
    --log-eps 1e-6
    --cmap magma
    --save-plot png
    --out ./png
    --no-show
"""

from __future__ import annotations
import argparse
import os
from typing import Literal, Dict, Any

import h5py
import numpy as np

import matplotlib.pyplot as plt

import pygsk.plot as plot_mod
plot_dyn = plot_mod.plot_dyn

# ----------------------------------------------------------------------
# Detect product type
# ----------------------------------------------------------------------

def _detect_product_type(f: h5py.File) -> Literal["skstream", "rfi"]:
    """Return SK-stream or RFI-cleaned."""
    if ("s1_xx_clean" in f or "s1_yy_clean" in f) and ("freq_block_hz" in f):
        return "rfi"
    if ("s1_xx" in f or "s1_yy" in f) and ("sk_flags_xx" in f or "sk_flags_yy" in f):
        return "skstream"
    raise ValueError("Cannot detect product type: not SK-stream or RFI-cleaned.")

# ----------------------------------------------------------------------
# Load SK-stream
# ----------------------------------------------------------------------

def _load_skstream(h5path: str) -> Dict[str, Any]:
    with h5py.File(h5path, "r") as f:
        if _detect_product_type(f) != "skstream":
            raise ValueError("File is not SK-stream.")

        freq = np.asarray(f["freq_hz"][:], float)
        time = np.asarray(f["time_blk"][:], float)

        data = {
            "product_type": "skstream",
            "freq": freq,
            "time": time,
            "has_xx": ("s1_xx" in f),
            "has_yy": ("s1_yy" in f),
        }

        if data["has_xx"]:
            data["s1_xx"] = np.asarray(f["s1_xx"][:], float)
            data["flags_xx"] = np.asarray(f["sk_flags_xx"][:], float)
        if data["has_yy"]:
            data["s1_yy"] = np.asarray(f["s1_yy"][:], float)
            data["flags_yy"] = np.asarray(f["sk_flags_yy"][:], float)

        attrs = {}
        for key in ("M", "N", "d", "pfa"):
            if key in f.attrs:
                attrs[key] = f.attrs[key]
        data["attrs"] = attrs

    return data

# ----------------------------------------------------------------------
# Load RFI-cleaned
# ----------------------------------------------------------------------

def _load_rfi(h5path: str) -> Dict[str, Any]:
    with h5py.File(h5path, "r") as f:
        if _detect_product_type(f) != "rfi":
            raise ValueError("File is not RFI-cleaned.")

        freq_blk = np.asarray(f["freq_block_hz"][:], float)
        time = np.asarray(f["time_blk"][:], float)

        data = {
            "product_type": "rfi",
            "freq_block": freq_blk,
            "time": time,
            "has_xx": ("s1_xx_clean" in f),
            "has_yy": ("s1_yy_clean" in f),
        }

        if data["has_xx"]:
            data["s1_xx_clean"] = np.asarray(f["s1_xx_clean"][:], float)
            data["mask_xx"] = np.asarray(f["mask_xx"][:], float)

        if data["has_yy"]:
            data["s1_yy_clean"] = np.asarray(f["s1_yy_clean"][:], float)
            data["mask_yy"] = np.asarray(f["mask_yy"][:], float)

        attrs = {}
        for key in ("M", "N", "d", "pfa", "F_block", "flag_mode", "F_eff", "n_blocks"):
            if key in f.attrs:
                attrs[key] = f.attrs[key]
        data["attrs"] = attrs

    return data

# ----------------------------------------------------------------------
# Annotation and save-name helpers
# ----------------------------------------------------------------------

def _annotate(ax: plt.Axes, lines: list[str]) -> None:
    if not lines:
        return
    ax.text(
        0.01, 0.99,
        "\n".join(lines),
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=8,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
    )


def _make_save_path(h5path: str, product: str, pol_mode: str, ext: str, outdir: str) -> str:
    base = os.path.splitext(os.path.basename(h5path))[0]
    tag = "quick_rfi" if product == "rfi" else "quick_skstream"
    if pol_mode in ("XX", "YY"):
        fname = f"{base}_{tag}_{pol_mode}.{ext}"
    else:
        fname = f"{base}_{tag}.{ext}"
    return os.path.join(outdir, fname)

# ----------------------------------------------------------------------
# Plotting: SK-stream products
# ----------------------------------------------------------------------

def _plot_skstream(
    h5path: str,
    data: Dict[str, Any],
    pol: str,
    scale: str,
    vmin: float | None,
    vmax: float | None,
    log_eps: float | None,
    cmap: str,
    dpi: int,
    transparent: bool,
    save_plot: str | None,
    outdir: str,
    no_show: bool,
) -> None:
    """
    Quicklook for SK-stream products:
        S1 (top), SK flags (bottom), per polarization.
    """
    time = data["time"]
    freq = data["freq"]
    has_xx = data["has_xx"]
    has_yy = data["has_yy"]
    attrs = data["attrs"]

    pol = pol.upper()
    if pol not in ("XX", "YY", "BOTH"):
        raise ValueError("--pol must be XX, YY, or both")

    plot_xx = has_xx and (pol in ("XX", "BOTH"))
    plot_yy = has_yy and (pol in ("YY", "BOTH"))

    if not (plot_xx or plot_yy):
        raise ValueError("Requested polarization(s) not present in SK-stream file.")

    ncols = 2 if (plot_xx and plot_yy) else 1
    nrows = 2

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(10.0 if ncols == 1 else 12.0, 6.0),
        sharex="col",
        sharey="row",
    )

    # Ensure axes is 2D [row, col]
    axes = np.asarray(axes)
    if axes.ndim == 1:
        axes = np.vstack([axes, axes]) if nrows == 1 else axes.reshape(nrows, 1)

    def _panel(pol_label: str, col: int) -> None:
        if pol_label == "XX":
            s1 = data["s1_xx"]
            flags = data["flags_xx"]
        else:
            s1 = data["s1_yy"]
            flags = data["flags_yy"]

        # Top: S1
        ax_top = axes[0, col]
        plot_dyn(
            s1,
            time=time,
            freq_hz=freq,
            title=f"S1 ({pol_label})",
            cbar_label="S1 (arb.)",
            show=False,
            save_path=None,
            dpi=dpi,
            transparent=transparent,
            figsize=(6.0, 3.0),
            ax=ax_top,
            scale=scale,
            vmin=vmin,
            vmax=vmax,
            log_eps=log_eps,
            cmap=cmap,
        )

        # Bottom: SK flags
        ax_bot = axes[1, col]
        plot_dyn(
            flags,
            time=time,
            freq_hz=freq,
            title=f"SK flags ({pol_label})",
            cbar_label="flag",
            show=False,
            save_path=None,
            dpi=dpi,
            transparent=transparent,
            figsize=(6.0, 3.0),
            ax=ax_bot,
            scale="linear",
            vmin=None,
            vmax=None,
            log_eps=None,
            cmap="viridis",
            is_categorical=True,
        )
        # Per-pol annotation: SK parameters + fraction flagged (total / hi / lo)
        n_tot = flags.size

        # SK>hi → flags > 0 ; SK<lo → flags < 0
        n_hi = int(np.count_nonzero(flags > 0))
        n_lo = int(np.count_nonzero(flags < 0))
        n_bad = n_hi + n_lo

        if n_tot > 0:
            frac_bad = (n_bad / n_tot) * 100.0
            frac_hi  = (n_hi  / n_tot) * 100.0
            frac_lo  = (n_lo  / n_tot) * 100.0
        else:
            frac_bad = frac_hi = frac_lo = np.nan

        lines = []
        if "M" in attrs:
            lines.append(f"M={int(attrs['M'])}")
        if "N" in attrs:
            lines.append(f"N={int(attrs['N'])}")
        if "d" in attrs:
            lines.append(f"d={float(attrs['d']):g}")
        if "pfa" in attrs:
            lines.append(f"pfa={float(attrs['pfa']):.3g}")

        lines.append(f"flagged total ≈ {frac_bad:.2f}%")
        lines.append(f"  SK>hi ≈ {frac_hi:.2f}%")
        lines.append(f"  SK<lo ≈ {frac_lo:.2f}%")

        _annotate(ax_bot, lines)


    col = 0
    if plot_xx:
        _panel("XX", col)
        col += 1
    if plot_yy:
        _panel("YY", col)

    fig.tight_layout()

    if save_plot:
        os.makedirs(outdir, exist_ok=True)
        path = _make_save_path(h5path, "skstream", pol, save_plot, outdir)
        print(f"[INFO] Saving SK-stream quicklook to: {path}")
        fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")

    if not no_show:
        plt.show()

    plt.close(fig)


# ----------------------------------------------------------------------
# Plotting: RFI-cleaned products
# ----------------------------------------------------------------------

# def _plot_rfi(
    # h5path: str,
    # data: Dict[str, Any],
    # pol: str,
    # scale: str,
    # vmin: float | None,
    # vmax: float | None,
    # log_eps: float | None,
    # cmap: str,
    # dpi: int,
    # transparent: bool,
    # save_plot: str | None,
    # outdir: str,
    # no_show: bool,
# ) -> None:
    # """
    # Quicklook for RFI-cleaned products:
        # Top:  S1_clean (per-pol)
        # Bot:  good-channel counts per block (0..F_block).
    # """
    # time = data["time"]
    # freq_block = data["freq_block"]
    # has_xx = data["has_xx"]
    # has_yy = data["has_yy"]
    # attrs = data["attrs"]

    # F_block = int(attrs.get("F_block", 1))
    # flag_mode = str(attrs.get("flag_mode", "unknown"))

    # pol = pol.upper()
    # if pol not in ("XX", "YY", "BOTH"):
        # raise ValueError("--pol must be XX, YY, or both")

    # plot_xx = has_xx and (pol in ("XX", "BOTH"))
    # plot_yy = has_yy and (pol in ("YY", "BOTH"))

    # if not (plot_xx or plot_yy):
        # raise ValueError("Requested polarization(s) not present in RFI-cleaned file.")

    # ncols = 2 if (plot_xx and plot_yy) else 1
    # nrows = 2

    # fig, axes = plt.subplots(
        # nrows=nrows,
        # ncols=ncols,
        # figsize=(10.0 if ncols == 1 else 12.0, 6.0),
        # sharex="col",
        # sharey="row",
    # )

    # axes = np.asarray(axes)
    # if axes.ndim == 1:
        # axes = np.vstack([axes, axes]) if nrows == 1 else axes.reshape(nrows, 1)

    # def _panel(pol_label: str, col: int) -> None:
        # if pol_label == "XX":
            # s1_clean = data["s1_xx_clean"]
            # mask = data["mask_xx"]
        # else:
            # s1_clean = data["s1_yy_clean"]
            # mask = data["mask_yy"]

        # T, n_blocks = s1_clean.shape

        # # Top: S1_clean
        # ax_top = axes[0, col]
        # plot_dyn(
            # s1_clean,
            # time=time,
            # freq_hz=freq_block,
            # title=f"S1_clean ({pol_label})",
            # cbar_label="S1 (arb.)",
            # show=False,
            # save_path=None,
            # dpi=dpi,
            # transparent=transparent,
            # figsize=(6.0, 3.0),
            # ax=ax_top,
            # scale=scale,
            # vmin=vmin,
            # vmax=vmax,
            # log_eps=log_eps,
            # cmap=cmap,
        # )

        # # Bottom: good-channel count
        # ax_bot = axes[1, col]
        # plot_dyn(
            # mask,
            # time=time,
            # freq_hz=freq_block,
            # title=f"Good channels per block ({pol_label})",
            # cbar_label="N_good",
            # show=False,
            # save_path=None,
            # dpi=dpi,
            # transparent=transparent,
            # figsize=(6.0, 3.0),
            # ax=ax_bot,
            # scale="linear",
            # vmin=0.0,
            # vmax=float(F_block),
            # log_eps=None,
            # cmap="viridis",
        # )

        # # Fraction flagged (based on mask counts)
        # total_chan = T * n_blocks * F_block
        # good_chan = float(np.sum(mask))
        # frac_flagged = (1.0 - good_chan / total_chan) * 100.0 if total_chan > 0 else np.nan

        # lines = []
        # if "M" in attrs:
            # lines.append(f"M={int(attrs['M'])}")
        # if "N" in attrs:
            # lines.append(f"N={int(attrs['N'])}")
        # if "d" in attrs:
            # lines.append(f"d={float(attrs['d']):g}")
        # if "pfa" in attrs:
            # lines.append(f"pfa={float(attrs['pfa']):.3g}")
        # lines.append(f"F_block={F_block}")
        # lines.append(f"flag_mode={flag_mode}")
        # lines.append(f"flagged ≈ {frac_flagged:.2f}%")

        # _annotate(ax_bot, lines)

    # col = 0
    # if plot_xx:
        # _panel("XX", col)
        # col += 1
    # if plot_yy:
        # _panel("YY", col)

    # fig.tight_layout()

    # if save_plot:
        # os.makedirs(outdir, exist_ok=True)
        # path = _make_save_path(h5path, "rfi", pol, save_plot, outdir)
        # print(f"[INFO] Saving RFI quicklook to: {path}")
        # fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")

    # if not no_show:
        # plt.show()

    # plt.close(fig)

import matplotlib.colors as mcolors  # add near the top of the file

def _plot_rfi(
    h5path: str,
    data: Dict[str, Any],
    pol: str,
    scale: str,
    vmin: float | None,
    vmax: float | None,
    log_eps: float | None,
    cmap: str,
    dpi: int,
    transparent: bool,
    save_plot: str | None,
    outdir: str,
    no_show: bool,
) -> None:
    """
    Quicklook for RFI-cleaned products:
        Top:  S1_clean (per-pol)
        Bot:  good-channel counts per block (0..F_block).
    """
    time = data["time"]
    freq_block = data["freq_block"]
    has_xx = data["has_xx"]
    has_yy = data["has_yy"]
    attrs = data["attrs"]

    F_block = int(attrs.get("F_block", 1))
    flag_mode = str(attrs.get("flag_mode", "unknown"))

    pol = pol.upper()
    if pol not in ("XX", "YY", "BOTH"):
        raise ValueError("--pol must be XX, YY, or both")

    plot_xx = has_xx and (pol in ("XX", "BOTH"))
    plot_yy = has_yy and (pol in ("YY", "BOTH"))

    if not (plot_xx or plot_yy):
        raise ValueError("Requested polarization(s) not present in RFI-cleaned file.")

    ncols = 2 if (plot_xx and plot_yy) else 1
    nrows = 2

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(10.0 if ncols == 1 else 12.0, 6.0),
        sharex="col",
        sharey="row",
    )

    axes = np.asarray(axes)
    if axes.ndim == 1:
        axes = axes.reshape(nrows, 1)

    def _panel(pol_label: str, col: int) -> None:
        """
        Draw one column (XX or YY):
          - top:  S1_clean
          - bottom: N_good (good channels per block), discrete 0..F_block
        """
        if pol_label == "XX":
            s1_clean = data["s1_xx_clean"]
            mask = data["mask_xx"]          # N_good, shape (T, n_blocks)
        else:
            s1_clean = data["s1_yy_clean"]
            mask = data["mask_yy"]

        T, n_blocks = s1_clean.shape

        # ------------------------------
        # TOP: S1_clean (use plot_dyn)
        # ------------------------------
        ax_top = axes[0, col]
        plot_dyn(
            s1_clean,
            time=time,
            freq_hz=freq_block,
            title=f"S1_clean ({pol_label})",
            cbar_label="S1 (arb.)",
            show=False,
            save_path=None,
            dpi=dpi,
            transparent=transparent,
            figsize=(6.0, 3.0),
            ax=ax_top,
            scale=scale,
            vmin=vmin,
            vmax=vmax,
            log_eps=log_eps,
            cmap=cmap,
        )

        # ---------------------------------------------
        # BOTTOM: N_good, discrete 0..F_block (no blur)
        # ---------------------------------------------
        ax_bot = axes[1, col]

        # Discrete colormap: one color per integer 0..F_block
        levels = np.arange(F_block + 2) - 0.5         # boundaries: -0.5, 0.5, ..., F+0.5
        # --- Discrete colormap for N_good (0..F_block) ---
        # Goal:
        #   0        -> black
        #   F_block  -> white
        #   1..F_block-1 -> distinct intermediate colors

        # Create a base colormap with enough distinct colors
        base_cmap = plt.get_cmap("tab20", F_block + 1)
        colors = base_cmap(np.arange(F_block + 1))

        # Force 0 → black
        colors[0] = [0.0, 0.0, 0.0, 1.0]     # black

        # Force F_block → white
        colors[-1] = [1.0, 1.0, 1.0, 1.0]    # white

        # Build a ListedColormap to prevent interpolation
        cmapN = mcolors.ListedColormap(colors)

        # Midpoints: boundaries at -0.5, 0.5, 1.5, ..., F_block + 0.5
        levels = np.arange(F_block + 2) - 0.5
        normN = mcolors.BoundaryNorm(levels, cmapN.N)


        extent = [time[0], time[-1], freq_block[0], freq_block[-1]]

        # IMPORTANT: transpose so y=freq, x=time (like plot_dyn)
        im = ax_bot.imshow(
            mask.T,                     # shape (n_blocks, T) → y=freq, x=time
            origin="lower",
            aspect="auto",
            extent=extent,
            cmap=cmapN,
            norm=normN,
            interpolation="nearest",    # no smoothing between integers
        )

        ax_bot.set_xlabel("Time [s]")
        ax_bot.set_ylabel("Frequency [Hz]")
        ax_bot.set_title(f"Good channels per block ({pol_label})")

        # Discrete colorbar ticks at 0..F_block
        cbar = fig.colorbar(im, ax=ax_bot, fraction=0.046, pad=0.04)
        cbar.set_label("N_good")
        cbar.set_ticks(range(F_block + 1))
        cbar.set_ticklabels([str(i) for i in range(F_block + 1)])

        # ------------------------------
        # Annotation box (meta + stats)
        # ------------------------------
        # mask holds N_good in [0..F_block]
        total_chan = T * n_blocks * F_block
        good_chan = float(np.sum(mask))
        frac_flagged = (
            (1.0 - good_chan / total_chan) * 100.0 if total_chan > 0 else np.nan
        )

        lines = []
        if "M" in attrs:
            lines.append(f"M={int(attrs['M'])}")
        if "N" in attrs:
            lines.append(f"N={int(attrs['N'])}")
        if "d" in attrs:
            lines.append(f"d={float(attrs['d']):g}")
        if "pfa" in attrs:
            lines.append(f"pfa={float(attrs['pfa']):.3g}")
        lines.append(f"F_block={F_block}")
        lines.append(f"flag_mode={flag_mode}")
        lines.append(f"flagged ≈ {frac_flagged:.2f}%")

        _annotate(ax_bot, lines)

    col = 0
    if plot_xx:
        _panel("XX", col)
        col += 1
    if plot_yy:
        _panel("YY", col)

    fig.tight_layout()

    if save_plot:
        os.makedirs(outdir, exist_ok=True)
        path = _make_save_path(h5path, "rfi", pol, save_plot, outdir)
        print(f"[INFO] Saving RFI quicklook to: {path}")
        fig.savefig(path, dpi=dpi, transparent=transparent, bbox_inches="tight")

    if not no_show:
        plt.show()

    plt.close(fig)

# ----------------------------------------------------------------------
# main()
# ----------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Unified OVRO-LWA quicklook for SK-stream and RFI-cleaned products."
    )
    ap.add_argument(
        "h5file",
        type=str,
        help="Input HDF5 file (SK-stream or RFI-cleaned).",
    )
    ap.add_argument(
        "--pol",
        type=str,
        default="both",
        choices=["XX", "YY", "both"],
        help="Which polarization(s) to plot (default: both).",
    )
    ap.add_argument(
        "--scale",
        type=str,
        default="linear",
        choices=["linear", "log"],
        help="Scaling for S1 panels (default: linear).",
    )
    ap.add_argument(
        "--vmin",
        type=float,
        default=None,
        help="Lower bound for S1 color scaling.",
    )
    ap.add_argument(
        "--vmax",
        type=float,
        default=None,
        help="Upper bound for S1 color scaling.",
    )
    ap.add_argument(
        "--log-eps",
        type=float,
        default=None,
        help="Floor for log scaling.",
    )
    ap.add_argument(
        "--cmap",
        type=str,
        default="viridis",
        help="Matplotlib colormap for S1 panels.",
    )
    ap.add_argument(
        "--save-plot",
        type=str,
        default=None,
        help="If set (e.g. 'png', 'pdf'), save figure with this extension.",
    )
    ap.add_argument(
        "--out",
        type=str,
        default=".",
        help="Output directory for saved figure (default: current directory).",
    )
    ap.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Figure DPI for saved plots.",
    )
    ap.add_argument(
        "--transparent",
        action="store_true",
        help="Save figures with transparent background.",
    )
    ap.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display the figure (useful on headless systems).",
    )

    args = ap.parse_args()

    h5path = args.h5file
    if not os.path.exists(h5path):
        raise FileNotFoundError(h5path)

    # Detect product type
    with h5py.File(h5path, "r") as f:
        product_type = _detect_product_type(f)

    print(f"[INFO] Detected product type: {product_type}")

    if product_type == "skstream":
        data = _load_skstream(h5path)
        _plot_skstream(
            h5path=h5path,
            data=data,
            pol=args.pol,
            scale=args.scale,
            vmin=args.vmin,
            vmax=args.vmax,
            log_eps=args.log_eps,
            cmap=args.cmap,
            dpi=args.dpi,
            transparent=args.transparent,
            save_plot=args.save_plot,
            outdir=args.out,
            no_show=args.no_show,
        )
    else:
        data = _load_rfi(h5path)
        _plot_rfi(
            h5path=h5path,
            data=data,
            pol=args.pol,
            scale=args.scale,
            vmin=args.vmin,
            vmax=args.vmax,
            log_eps=args.log_eps,
            cmap=args.cmap,
            dpi=args.dpi,
            transparent=args.transparent,
            save_plot=args.save_plot,
            outdir=args.out,
            no_show=args.no_show,
        )


if __name__ == "__main__":
    main()
