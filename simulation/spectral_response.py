"""
spectral_response.py
====================
Compute the through- and drop-port spectral response of a racetrack
microring resonator using the Transfer-Matrix Method (TMM) / coupled-mode
theory analytical model.

For full FDTD verification, the script can be extended to call MEEP
(see the ``meep_simulation()`` function stub).

Outputs
-------
- spectra_8ch.png   — drop/through spectra for all 8 channels
- metrics.csv       — IL, ER, Q, FWHM, shape factor per channel

Run::

    python spectral_response.py
    python spectral_response.py --channels 4 --plot_single 3
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Platform / ring parameters (imported from design layer)
# ---------------------------------------------------------------------------
_design_dir = Path(__file__).resolve().parent.parent / "design"
sys.path.insert(0, str(_design_dir))

import config as cfg

# Speed of light in nm/s
_C_NM_S = 2.998e17


# ---------------------------------------------------------------------------
# Transfer-matrix model of symmetric add-drop racetrack MRR
# ---------------------------------------------------------------------------

def _round_trip_length(lc: float, r: float = cfg.BEND_RADIUS) -> float:
    """Total round-trip optical path length [um]."""
    return 2 * lc + 2 * math.pi * r


def _alpha_field(loss_db_per_cm: float = 2.0) -> float:
    """Convert propagation loss (dB/cm) to field amplitude loss per um."""
    alpha_per_cm = loss_db_per_cm * math.log(10) / 20.0
    return alpha_per_cm / 1e4   # per um


def ring_spectrum(
    wl_nm: np.ndarray,
    lc: float,
    kappa_sq: float = 0.10,
    loss_db_per_cm: float = 2.0,
    n_eff_fn=None,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute through and drop power transmission vs wavelength.

    Uses the analytical transfer matrix for a symmetric add-drop MRR:
        T_through = |t*(t*^2 - a*exp(iφ)) / (1 - t^2*a*exp(iφ))|²  (approx)
        T_drop    = (κ²*a^(1/2)) / |1 - t^2*a*exp(iφ)|²

    Parameters
    ----------
    wl_nm       : 1-D wavelength array [nm].
    lc          : Coupling-section length [um].
    kappa_sq    : Power coupling coefficient κ².
    loss_db_per_cm: Waveguide propagation loss [dB/cm].
    n_eff_fn    : Callable(wl_nm) -> n_eff; defaults to linear dispersion.

    Returns
    -------
    (T_through, T_drop) : Power transmission arrays, same shape as wl_nm.
    """
    if n_eff_fn is None:
        # Linear dispersion around 1550 nm
        def n_eff_fn(w):  # noqa: ANN001
            return cfg.N_EFF - (w - 1550.0) * 4e-4

    lrt = _round_trip_length(lc)
    alpha = _alpha_field(loss_db_per_cm)

    t_sq = 1.0 - kappa_sq          # through-coupler power transmission
    t    = math.sqrt(t_sq)
    a    = math.exp(-alpha * lrt)   # round-trip field amplitude transmission

    T_thru = np.empty_like(wl_nm, dtype=float)
    T_drop = np.empty_like(wl_nm, dtype=float)

    for i, wl in enumerate(wl_nm):
        neff = n_eff_fn(wl)
        phi  = 2 * math.pi * neff * lrt / (wl * 1e-3)  # phase [rad] (wl in um)

        # Denominator
        denom_sq = 1 - 2 * t_sq * a * math.cos(phi) + (t_sq * a) ** 2

        # Drop port (both couplers have same κ)
        # T_drop = κ⁴ · a / |1 − t²·a·exp(iφ)|²
        T_drop[i]  = (kappa_sq ** 2 * a) / denom_sq

        # Through port (symmetric add-drop transfer matrix)
        # T_thru = t² · |1 − a·exp(iφ)|² / |1 − t²·a·exp(iφ)|²
        num_thru   = t_sq * (1 - 2 * a * math.cos(phi) + a ** 2)
        T_thru[i]  = num_thru / denom_sq

    return T_thru, T_drop


# ---------------------------------------------------------------------------
# Metric extraction
# ---------------------------------------------------------------------------

def extract_metrics(
    wl_nm: np.ndarray,
    T_drop: np.ndarray,
    T_thru: np.ndarray,
    center_nm: float | None = None,
    search_window_nm: float = 4.0,
) -> dict:
    """Extract IL, ER, Q, FWHM, shape factor from spectral data.

    Parameters
    ----------
    wl_nm           : Wavelength array [nm].
    T_drop          : Drop-port power transmission (linear).
    T_thru          : Through-port power transmission (linear).
    center_nm       : Expected resonance wavelength [nm].  When provided the
                      peak search and bandwidth extraction are restricted to a
                      ±search_window_nm window, preventing multi-FSR artifacts.
    search_window_nm: Half-window around *center_nm* for local peak search.
    """
    # --- Peak search (local or global) ------------------------------------
    if center_nm is not None:
        mask = np.abs(wl_nm - center_nm) <= search_window_nm
        local_idx = np.argmax(T_drop[mask])
        peak_idx  = int(np.where(mask)[0][local_idx])
    else:
        peak_idx = int(np.argmax(T_drop))

    peak_wl  = wl_nm[peak_idx]
    peak_T   = T_drop[peak_idx]
    trough_T = T_thru[peak_idx]

    # Insertion loss [dB] — drop port IL relative to input
    il_db = -10 * math.log10(max(peak_T, 1e-12))

    # Extinction ratio [dB] — through port suppression at resonance
    er_db = -10 * math.log10(max(trough_T, 1e-12))

    # --- Bandwidth extraction (local window to avoid spanning multiple FSRs)
    local_mask = np.abs(wl_nm - peak_wl) <= search_window_nm
    wl_local   = wl_nm[local_mask]
    Td_local   = T_drop[local_mask]

    # 3-dB bandwidth (FWHM)
    half_max = peak_T / 2.0
    above    = wl_local[Td_local >= half_max]
    fwhm_nm  = float(above[-1] - above[0]) if len(above) >= 2 else float("nan")

    # Quality factor
    q_factor = peak_wl / fwhm_nm if (not math.isnan(fwhm_nm) and fwhm_nm > 0) else float("nan")

    # 1-dB bandwidth
    tenth_max = peak_T * 10 ** (-1.0 / 10.0)
    above_1db = wl_local[Td_local >= tenth_max]
    bw_1db_nm = float(above_1db[-1] - above_1db[0]) if len(above_1db) >= 2 else float("nan")

    shape_factor = (bw_1db_nm / fwhm_nm
                    if (not math.isnan(fwhm_nm) and fwhm_nm > 0)
                    else float("nan"))

    # FSR: distance to nearest secondary resonance peak
    prominence_threshold = peak_T * 0.1
    secondary_peaks = []
    for i in range(1, len(wl_nm) - 1):
        if T_drop[i] > T_drop[i - 1] and T_drop[i] > T_drop[i + 1]:
            if i != peak_idx and T_drop[i] > prominence_threshold:
                secondary_peaks.append(wl_nm[i])
    fsr_nm = float("nan")
    if secondary_peaks:
        dists = [abs(sp - peak_wl) for sp in secondary_peaks]
        fsr_nm = round(min(dists), 4)

    return {
        "peak_wl_nm":    round(peak_wl, 3),
        "il_db":         round(il_db, 2),
        "er_db":         round(er_db, 2),
        "fwhm_nm":       round(fwhm_nm, 4),
        "q_factor":      round(q_factor, 0) if not math.isnan(q_factor) else float("nan"),
        "shape_factor":  round(shape_factor, 3) if not math.isnan(shape_factor) else float("nan"),
        "fsr_nm":        fsr_nm,
    }


# ---------------------------------------------------------------------------
# Multi-channel spectral plot
# ---------------------------------------------------------------------------

def _itu_channel_wl(k: int) -> float:
    """Return ITU C-band channel wavelength [nm] for 0-indexed channel k."""
    return cfg.FIRST_CHANNEL_NM + k * cfg.CHANNEL_SPACING_NM


def _coupling_len_for_channel(k: int) -> float:
    """Compute per-channel coupling length (imported logic)."""
    target_nm = _itu_channel_wl(k)
    target_um = target_nm / 1000.0
    circ = 2 * math.pi * cfg.BEND_RADIUS
    nominal_lrt = 2 * cfg.COUPLING_LEN + circ
    m = round(cfg.N_EFF * nominal_lrt / target_um)
    lrt = m * target_um / cfg.N_EFF
    return max((lrt - circ) / 2.0, 1.0)


def simulate_all_channels(
    num_channels: int = cfg.NUM_CHANNELS,
    wl_start: float = 1530.0,
    wl_stop:  float = 1565.0,
    n_points: int   = 3500,
    kappa_sq: float = 0.08,
) -> dict:
    """Simulate all DWDM channels and return spectral data + metrics."""
    wl = np.linspace(wl_start, wl_stop, n_points)
    results = {}

    for k in range(num_channels):
        lc = _coupling_len_for_channel(k)
        target_nm = _itu_channel_wl(k)

        # Dispersion slope dn/dλ derived from n_g = n_eff − λ·dn/dλ:
        # dn/dλ = (n_eff − n_g) / λ₀  (units: nm⁻¹)
        _slope = (cfg.N_EFF - cfg.N_GROUP) / target_nm   # ≈ −1.126e-3 nm⁻¹

        def n_fn(w, lam0=target_nm, slope=_slope):  # noqa: ANN001
            return cfg.N_EFF + (w - lam0) * slope

        T_thru, T_drop = ring_spectrum(wl, lc=lc, kappa_sq=kappa_sq,
                                       n_eff_fn=n_fn)
        metrics = extract_metrics(wl, T_drop, T_thru, center_nm=target_nm)
        results[k] = {
            "wl":      wl,
            "T_thru":  T_thru,
            "T_drop":  T_drop,
            "metrics": metrics,
            "target_nm": target_nm,
        }

    return results


def plot_spectra(
    results: dict,
    output_file: str = "spectra_8ch.png",
) -> None:
    """Plot through/drop spectra for all channels."""
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = plt.cm.tab10(np.linspace(0, 1, len(results)))

    for k, data in results.items():
        wl     = data["wl"]
        T_drop = 10 * np.log10(np.clip(data["T_drop"], 1e-12, None))
        T_thru = 10 * np.log10(np.clip(data["T_thru"], 1e-12, None))
        col    = colors[k]

        ax.plot(wl, T_drop, color=col, lw=1.5,
                label=f"Ch{k+1} drop ({data['target_nm']:.2f}nm)")
        ax.plot(wl, T_thru, color=col, lw=0.8, ls="--")

        # Mark ITU channel wavelength
        ax.axvline(data["target_nm"], color=col, lw=0.5, ls=":", alpha=0.7)

    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Transmission (dB)")
    ax.set_title("DWDM Demultiplexer — Through (dashed) and Drop (solid) Spectra")
    ax.set_ylim(-40, 2)
    ax.legend(fontsize=7, ncol=2, loc="lower left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"Saved: {output_file}")


def save_metrics_csv(results: dict, output_file: str = "metrics.csv") -> None:
    """Write per-channel metrics to CSV."""
    fieldnames = ["channel", "target_nm", "peak_wl_nm", "il_db", "er_db",
                  "fwhm_nm", "q_factor", "shape_factor", "fsr_nm"]
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for k, data in results.items():
            row = {"channel": k + 1, "target_nm": data["target_nm"]}
            row.update(data["metrics"])
            writer.writerow(row)
    print(f"Saved: {output_file}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Racetrack MRR spectral response simulation."
    )
    p.add_argument("--channels", type=int, default=cfg.NUM_CHANNELS)
    p.add_argument("--kappa",    type=float, default=0.08,
                   help="Power coupling coefficient κ² (default: %(default)s)")
    p.add_argument("--output_dir", type=str, default=".",
                   help="Directory for output files (default: %(default)s)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    out  = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Simulating {args.channels} DWDM channels …")
    results = simulate_all_channels(
        num_channels=args.channels,
        kappa_sq=args.kappa,
    )

    for k, data in results.items():
        m = data["metrics"]
        print(
            f"  Ch{k+1:2d}  λ={data['target_nm']:.2f}nm  "
            f"peak={m['peak_wl_nm']:.3f}nm  "
            f"IL={m['il_db']:.1f}dB  ER={m['er_db']:.1f}dB  "
            f"Q={m['q_factor']:.0f}"
        )

    plot_spectra(results, output_file=str(out / "spectra_8ch.png"))
    save_metrics_csv(results, output_file=str(out / "metrics.csv"))
