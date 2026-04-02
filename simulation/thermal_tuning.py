"""
thermal_tuning.py
=================
Model and visualise the thermal tuning of racetrack MRR resonances.

Physics:
  Δλ_res = (λ_res / n_g) * Γ * (dn/dT) * ΔT
  ΔT     = R_th * P_heater    (linear thermal model)

Outputs:
  - thermal_tuning.png   — resonance shift vs heater power
  - thermal_map.png      — 2-D temperature profile (Gaussian approximation)

Run::

    python thermal_tuning.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Access design config
_design_dir = Path(__file__).resolve().parent.parent / "design"
sys.path.insert(0, str(_design_dir))
import config as cfg


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
DN_DT_SI   = 1.84e-4    # thermo-optic coefficient of Si [1/K]
GAMMA      = 0.90       # confinement factor in Si core
R_TH       = 11.2       # thermal resistance of heater [K/mW]
                         # (from 2-D FEM thermal simulation, COMSOL)
# Resulting tuning efficiency η = (λ/n_g)·Γ·(dn/dT)·R_th
# ≈ (1550/4.182)·0.9·1.84e-4·11.2 × 1000 pm/nm ≈ 688 pm/mW


# ---------------------------------------------------------------------------
# Tuning model
# ---------------------------------------------------------------------------

def resonance_shift_nm(
    power_mw: float | np.ndarray,
    lambda0_nm: float = 1550.0,
    n_g: float = cfg.N_GROUP,
    dn_dt: float = DN_DT_SI,
    gamma: float = GAMMA,
    r_th: float = R_TH,
) -> float | np.ndarray:
    """Compute resonance shift [nm] for a given heater power [mW].

    Δλ = (λ₀ / n_g) * Γ * (dn/dT) * R_th * P
    """
    delta_T = r_th * power_mw
    return (lambda0_nm / n_g) * gamma * dn_dt * delta_T


def power_for_shift(
    shift_nm: float,
    lambda0_nm: float = 1550.0,
    n_g: float = cfg.N_GROUP,
    dn_dt: float = DN_DT_SI,
    gamma: float = GAMMA,
    r_th: float = R_TH,
) -> float:
    """Compute heater power [mW] needed for a resonance shift of *shift_nm* nm."""
    if r_th == 0:
        return float("inf")
    delta_T_required = shift_nm * n_g / (lambda0_nm * gamma * dn_dt)
    return delta_T_required / r_th


def tuning_efficiency(
    lambda0_nm: float = 1550.0,
    n_g: float = cfg.N_GROUP,
    dn_dt: float = DN_DT_SI,
    gamma: float = GAMMA,
    r_th: float = R_TH,
) -> float:
    """Return tuning efficiency [pm/mW]."""
    return resonance_shift_nm(1.0, lambda0_nm, n_g, dn_dt, gamma, r_th) * 1e3


def thermal_crosstalk(
    pitch_um: float = 100.0,
    power_mw: float = 10.0,
    kappa_th: float = 148.0,    # thermal conductivity of Si [W/(m·K)]
    heater_len_um: float = 15.0,
) -> float:
    """Estimate temperature rise on a neighbouring ring [K].

    Uses an approximate line-source heat diffusion model.
    """
    # Simplified Green's function for a 2-D line source in an infinite medium
    # ΔT ≈ P / (2π κ L) — rough estimate
    power_w = power_mw * 1e-3
    length_m = heater_len_um * 1e-6
    distance_m = pitch_um * 1e-6
    delta_T = power_w / (2 * np.pi * kappa_th * length_m) * np.log(
        10 * heater_len_um / pitch_um + 1
    )
    return float(delta_T)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_tuning(
    lambda0_nm: float = 1550.0,
    max_power_mw: float = 100.0,
    output_file: str = "thermal_tuning.png",
) -> None:
    """Plot resonance shift and temperature rise vs heater power."""
    P = np.linspace(0, max_power_mw, 200)
    shift = resonance_shift_nm(P, lambda0_nm)
    delta_T = R_TH * P

    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax2 = ax1.twinx()

    ax1.plot(P, shift, "b-", lw=2, label="Resonance shift (nm)")
    ax2.plot(P, delta_T, "r--", lw=1.5, label="ΔT (K)")

    # Annotate tuning efficiency
    eta = tuning_efficiency(lambda0_nm)
    ax1.annotate(
        f"η = {eta:.1f} pm/mW",
        xy=(max_power_mw * 0.6, shift[int(len(P) * 0.6)]),
        xytext=(max_power_mw * 0.4, shift[int(len(P) * 0.6)] + 0.3),
        arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=9,
    )

    # Mark ITU channel-spacing shift
    channel_shift = cfg.CHANNEL_SPACING_NM
    ax1.axhline(channel_shift, color="green", ls=":", lw=1,
                label=f"ITU channel spacing ({channel_shift} nm)")

    ax1.set_xlabel("Heater power (mW)")
    ax1.set_ylabel("Resonance shift (nm)", color="b")
    ax2.set_ylabel("Temperature rise ΔT (K)", color="r")
    ax1.tick_params(axis="y", labelcolor="b")
    ax2.tick_params(axis="y", labelcolor="r")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)
    ax1.set_title("Thermal Tuning of Racetrack MRR Resonance")

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"Saved: {output_file}")


def plot_thermal_map(
    heater_power_mw: float = 10.0,
    pitch_um: float = 100.0,
    output_file: str = "thermal_map.png",
) -> None:
    """2-D Gaussian-approximated temperature distribution near the heater."""
    x = np.linspace(-2 * pitch_um, 2 * pitch_um, 400)
    y = np.linspace(-50, 50, 200)
    X, Y = np.meshgrid(x, y)

    sigma_x = 30.0  # um — thermal spreading along waveguide direction
    sigma_y = 15.0  # um — spreading across waveguide

    T_peak = R_TH * heater_power_mw
    T = T_peak * np.exp(
        -(X ** 2) / (2 * sigma_x ** 2) - (Y ** 2) / (2 * sigma_y ** 2)
    )

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.contourf(X, Y, T, levels=20, cmap="hot")
    plt.colorbar(im, ax=ax, label="ΔT (K)")

    # Mark adjacent ring positions
    for xi in [-pitch_um, pitch_um]:
        ax.axvline(xi, color="cyan", lw=1, ls="--", label=f"Adjacent ring @ ±{pitch_um:.0f}μm")

    ax.set_xlabel("x (μm) — along bus direction")
    ax.set_ylabel("y (μm) — transverse")
    ax.set_title(f"Thermal Map: P = {heater_power_mw} mW, Pitch = {pitch_um} μm")
    ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"Saved: {output_file}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    eta = tuning_efficiency()
    print(f"Tuning efficiency     : {eta:.2f} pm/mW")

    ch_shift = power_for_shift(cfg.CHANNEL_SPACING_NM)
    print(f"Power for 1 channel   : {ch_shift:.1f} mW")

    full_range = power_for_shift(2.0)
    print(f"Power for ±2 nm range : {full_range:.1f} mW")

    xtalk_dT = thermal_crosstalk(pitch_um=100.0, power_mw=ch_shift)
    xtalk_shift = resonance_shift_nm(xtalk_dT / R_TH) * 1000  # pm
    print(f"Thermal crosstalk ΔT  : {xtalk_dT:.3f} K  "
          f"→ shift ≈ {xtalk_shift:.1f} pm")

    plot_tuning()
    plot_thermal_map()
