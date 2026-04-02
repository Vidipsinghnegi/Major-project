"""
dwdm_demux.py
=============
Parametric 8-channel (or N-channel) DWDM demultiplexer layout generator
using gdsfactory.

Each channel is a thermally tunable racetrack MRR that addresses one ITU
C-band channel on the 100 GHz grid.

Usage (CLI)::

    python dwdm_demux.py --channels 8 --spacing_ghz 100 --output dwdm_8ch.gds

Usage (Python API)::

    from dwdm_demux import dwdm_demux
    c = dwdm_demux(num_channels=8)
    c.write_gds("dwdm_8ch.gds")
"""

from __future__ import annotations

import argparse
import math

import gdsfactory as gf

import config as cfg
from racetrack_mrr import racetrack_mrr


# ---------------------------------------------------------------------------
# Helper: compute per-channel coupling length for resonance at target λ
# ---------------------------------------------------------------------------

def _coupling_len_for_wavelength(
    target_nm: float,
    bend_radius: float = cfg.BEND_RADIUS,
    wg_width: float = cfg.WG_WIDTH,
    n_eff: float = cfg.N_EFF,
    n_group: float = cfg.N_GROUP,
) -> float:
    """Return the coupling-section length [um] that places the racetrack
    resonance at *target_nm* nanometres.

    The round-trip condition is  m * lambda = n_eff * L_rt
    where  L_rt = 2*L_c + 2*pi*R.

    We choose the mode order *m* such that L_c is closest to the nominal
    value (cfg.COUPLING_LEN).
    """
    target_m = target_nm * 1e-3  # nm -> um
    circumference = 2 * math.pi * bend_radius  # um

    # Find mode order m that gives L_c closest to nominal
    nominal_lrt = 2 * cfg.COUPLING_LEN + circumference
    m_float = n_eff * nominal_lrt / target_m
    m = round(m_float)

    lrt = m * target_m / n_eff
    lc = (lrt - circumference) / 2.0
    return max(lc, 1.0)   # guard against negative values


# ---------------------------------------------------------------------------
# Top-level demux cell
# ---------------------------------------------------------------------------

@gf.cell
def dwdm_demux(
    num_channels: int = cfg.NUM_CHANNELS,
    first_channel_nm: float = cfg.FIRST_CHANNEL_NM,
    channel_spacing_nm: float = cfg.CHANNEL_SPACING_NM,
    bend_radius: float = cfg.BEND_RADIUS,
    gap_bus: float = cfg.GAP_BUS_RING,
    gap_drop: float = cfg.GAP_RING_DROP,
    wg_width: float = cfg.WG_WIDTH,
    channel_pitch_y: float = cfg.CHANNEL_PITCH_Y,
    chip_margin: float = cfg.CHIP_MARGIN,
) -> gf.Component:
    """Generate a DWDM demultiplexer with *num_channels* racetrack MRRs.

    Parameters
    ----------
    num_channels:        Number of wavelength channels.
    first_channel_nm:    Centre wavelength of the first channel [nm].
    channel_spacing_nm:  Channel-to-channel wavelength spacing [nm].
    bend_radius:         Racetrack bend radius [um].
    gap_bus:             Bus-to-ring coupling gap [um].
    gap_drop:            Ring-to-drop coupling gap [um].
    wg_width:            Waveguide width [um].
    channel_pitch_y:     Vertical pitch between channels [um].
    chip_margin:         Margin from chip edge to first element [um].

    Returns
    -------
    gf.Component with ports labelled 'in', 'thru',
    'drop_0' … 'drop_{N-1}', 'add_0' … 'add_{N-1}'.
    """
    top = gf.Component()

    y_offset = 0.0

    for k in range(num_channels):
        target_nm = first_channel_nm + k * channel_spacing_nm
        lc = _coupling_len_for_wavelength(
            target_nm=target_nm,
            bend_radius=bend_radius,
            wg_width=wg_width,
        )
        label = f"ch{k+1}\n{target_nm:.2f}nm"

        ring = top << racetrack_mrr(
            bend_radius=bend_radius,
            coupling_len=lc,
            gap_bus=gap_bus,
            gap_drop=gap_drop,
            wg_width=wg_width,
            channel_label=label,
        )
        ring.move((chip_margin, y_offset))

        # Expose drop and add ports with unique names
        top.add_port(f"drop_{k}", port=ring.ports["drop"])
        top.add_port(f"add_{k}",  port=ring.ports["add"])

        # Connect 'thru' of channel k to 'in' of channel k+1 via a short
        # routing straight (only for k < num_channels-1)
        if k == 0:
            top.add_port("in", port=ring.ports["in"])
        if k == num_channels - 1:
            top.add_port("thru", port=ring.ports["thru"])

        y_offset += channel_pitch_y

    return top


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate a DWDM demultiplexer GDSII layout."
    )
    p.add_argument("--channels",     type=int,   default=cfg.NUM_CHANNELS,
                   help="Number of DWDM channels (default: %(default)s)")
    p.add_argument("--spacing_ghz",  type=float, default=100.0,
                   help="Channel spacing in GHz (default: %(default)s)")
    p.add_argument("--first_nm",     type=float,
                   default=cfg.FIRST_CHANNEL_NM,
                   help="First channel wavelength in nm (default: %(default)s)")
    p.add_argument("--output",       type=str,   default="dwdm_demux.gds",
                   help="Output GDS filename (default: %(default)s)")
    return p.parse_args()


def _ghz_to_nm(spacing_ghz: float, centre_nm: float = 1550.0) -> float:
    """Convert channel spacing from GHz to nm at *centre_nm* nanometres."""
    c_nm_per_s = 3e17  # speed of light in nm/s
    return spacing_ghz * 1e9 * centre_nm**2 / c_nm_per_s


if __name__ == "__main__":
    args = _parse_args()
    spacing_nm = _ghz_to_nm(args.spacing_ghz)

    component = dwdm_demux(
        num_channels=args.channels,
        first_channel_nm=args.first_nm,
        channel_spacing_nm=spacing_nm,
    )
    component.write_gds(args.output)
    print(f"Written: {args.output}")
    print(f"  Channels : {args.channels}")
    print(f"  Spacing  : {spacing_nm:.3f} nm ({args.spacing_ghz:.0f} GHz)")
    print(f"  Ports    : {list(component.ports.keys())}")
    print(f"  Bbox     : {component.bbox}")
