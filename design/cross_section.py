"""
cross_section.py
================
Compute and plot waveguide cross-sections (refractive-index profiles)
for the SOI racetrack MRR platform using gdsfactory cross-section utilities
and matplotlib.

Run::

    python cross_section.py          # saves cross_section_strip.png
"""

from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")   # non-interactive backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from config import WG_WIDTH, WG_HEIGHT, BOX_HEIGHT


def plot_strip_cross_section(
    wg_width: float = WG_WIDTH,
    wg_height: float = WG_HEIGHT,
    box_height: float = BOX_HEIGHT,
    clad_height: float = 2.0,
    output_file: str = "cross_section_strip.png",
) -> None:
    """Render the SOI strip waveguide cross-section (all dims in um)."""
    fig, ax = plt.subplots(figsize=(6, 4))

    # Substrate (Si)
    substrate = mpatches.Rectangle(
        (-2, -(box_height + 0.5)), 4, 0.5,
        linewidth=0.8, edgecolor="k", facecolor="#b0b0b0", label="Si substrate"
    )
    ax.add_patch(substrate)

    # BOX (SiO₂)
    box = mpatches.Rectangle(
        (-2, -box_height), 4, box_height,
        linewidth=0.8, edgecolor="k", facecolor="#d4e8ff", label="SiO₂ BOX"
    )
    ax.add_patch(box)

    # Waveguide core (Si)
    core = mpatches.Rectangle(
        (-wg_width / 2, 0), wg_width, wg_height,
        linewidth=0.8, edgecolor="k", facecolor="#ff8800", label="Si core"
    )
    ax.add_patch(core)

    # Top cladding (SiO₂)
    cladding = mpatches.Rectangle(
        (-2, wg_height), 4, clad_height,
        linewidth=0.8, edgecolor="k", facecolor="#d4e8ff",
        alpha=0.5, label="SiO₂ cladding"
    )
    ax.add_patch(cladding)

    # TiN heater (above waveguide)
    heater_w = 1.0  # um
    heater_h = 0.1  # um
    heater_y = wg_height + 1.0
    heater = mpatches.Rectangle(
        (-heater_w / 2, heater_y), heater_w, heater_h,
        linewidth=0.8, edgecolor="k", facecolor="#aa44cc", label="TiN heater"
    )
    ax.add_patch(heater)

    # Annotations
    ax.annotate(
        f"w = {wg_width*1e3:.0f} nm",
        xy=(0, wg_height / 2), xytext=(wg_width / 2 + 0.3, wg_height / 2),
        arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=8,
    )
    ax.annotate(
        f"h = {wg_height*1e3:.0f} nm",
        xy=(wg_width / 2, wg_height / 2),
        xytext=(wg_width / 2 + 0.3, wg_height + 0.2),
        arrowprops=dict(arrowstyle="->", lw=0.8), fontsize=8,
    )

    ax.set_xlim(-2, 2)
    ax.set_ylim(-(box_height + 0.6), wg_height + clad_height + 0.2)
    ax.set_xlabel("x (μm)")
    ax.set_ylabel("y (μm)")
    ax.set_title("SOI Strip Waveguide Cross-Section")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    print(f"Saved: {output_file}")


if __name__ == "__main__":
    plot_strip_cross_section()
