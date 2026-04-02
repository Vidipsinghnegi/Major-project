"""Bilateral 12-channel DWDM add-drop ring filter (GDSFactory layout)
======================================================================
Based on paper Fig. 5 and Table 3.

Architecture
------------
A single horizontal bus waveguide carries all 12 wavelength channels.
Six pairs of racetrack ring resonators are placed **bilaterally**:

  Pair p  (p = 0 … 5):
    x_pair = MARGIN + p × CH_PITCH                          [µm]
    Odd  channel  ch = 2p + 1  →  ring_double ABOVE the bus  (y > 0)
    Even channel  ch = 2p + 2  →  ring_double BELOW the bus  (y < 0)

Key dimensions (paper Table 3)
-------------------------------
  BUS_LENGTH      = 2 × 15 + 6 × 35 = 240 µm
  CH_PITCH        =  35 µm   (consecutive pair pitch)
  SAME_SIDE_PITCH =  70 µm   (= 2 × CH_PITCH; same-side ring pitch)
  RING_FOOTPRINT  =  16 µm   (= Lc + 2R; Lc = 6 µm, R = 5 µm)
  BUS_GAP         =   0.2 µm (ring-to-bus coupling gap)

Bilateral pair x-positions
--------------------------
  Pair 0 : x = 15 µm   (R1 above, R2 below)
  Pair 1 : x = 50 µm   (R3 above, R4 below)
  Pair 2 : x = 85 µm   (R5 above, R6 below)
  Pair 3 : x = 120 µm  (R7 above, R8 below)
  Pair 4 : x = 155 µm  (R9 above, R10 below)
  Pair 5 : x = 190 µm  (R11 above, R12 below)

Usage
-----
  python design/ring_filter_bilateral.py
  # → writes ring_filter_bilateral.gds to the current directory

  # Programmatic:
  import gdsfactory as gf
  gf.gpdk.PDK.activate()
  from design.ring_filter_bilateral import bilateral_ring_filter
  c = bilateral_ring_filter()
"""

import gdsfactory as gf

# ── Activate the generic process design kit ────────────────────────────────────
gf.gpdk.PDK.activate()

# ── Design parameters (paper Table 3) ─────────────────────────────────────────
N_CH = 12             # total wavelength channels
N_PAIRS = N_CH // 2   # = 6  bilateral ring pairs

MARGIN = 15.0         # µm  bus straight margin at each end
CH_PITCH = 35.0       # µm  consecutive (pair-to-pair) pitch
SAME_SIDE_PITCH = 2 * CH_PITCH   # = 70 µm  (same-side ring-to-ring spacing)
BUS_LENGTH = 2 * MARGIN + N_PAIRS * CH_PITCH   # = 240 µm

RING_RADIUS = 5.0     # µm  racetrack bend radius
RING_LX = 6.0         # µm  racetrack straight coupling length
#                           footprint = 2 × RING_RADIUS + RING_LX = 16 µm  ✓
RING_LY = 0.01        # µm  racetrack side straight (minimal)
BUS_GAP = 0.2         # µm  ring-to-bus coupling gap


# ── Ring unit component (above-bus orientation by default) ─────────────────────
@gf.cell
def ring_unit(
    radius: float = RING_RADIUS,
    length_x: float = RING_LX,
    length_y: float = RING_LY,
    gap: float = BUS_GAP,
) -> gf.Component:
    """Racetrack add-drop ring resonator.

    Default orientation: ring body ABOVE the bus.

    Ports
    -----
    o1  : bus input  (left,  y = 0)
    o2  : bus through (right, y = 0)
    o3  : add port   (left,  y ≈ ring_height)
    o4  : drop port  (right, y ≈ ring_height)
    """
    return gf.components.ring_double(
        radius=radius,
        length_x=length_x,
        length_y=length_y,
        gap=gap,
    )


# ── Bilateral 12-channel ring filter ──────────────────────────────────────────
@gf.cell
def bilateral_ring_filter(
    n_pairs: int = N_PAIRS,
    margin: float = MARGIN,
    ch_pitch: float = CH_PITCH,
    ring_radius: float = RING_RADIUS,
    ring_lx: float = RING_LX,
    ring_ly: float = RING_LY,
    bus_gap: float = BUS_GAP,
) -> gf.Component:
    """Bilateral 12-channel DWDM add-drop ring filter.

    Odd  channels (ch = 1, 3, 5,  7,  9, 11) → rings ABOVE the bus.
    Even channels (ch = 2, 4, 6,  8, 10, 12) → rings BELOW the bus.
    Each pair occupies the **same x-position** on the bus.

    Parameters
    ----------
    n_pairs    : number of channel pairs (6 → 12 channels total)
    margin     : bus straight margin at each end [µm]
    ch_pitch   : pair-to-pair (consecutive) pitch [µm];
                 same-side pitch = 2 × ch_pitch = 70 µm
    ring_radius: racetrack bend radius [µm]
    ring_lx    : racetrack straight coupling length [µm];
                 ring footprint = 2 × ring_radius + ring_lx = 16 µm
    ring_ly    : racetrack side straight length [µm] (minimal)
    bus_gap    : ring-to-bus evanescent coupling gap [µm]

    Exposed ports
    -------------
    o_in            : bus input  (left end of bus)
    o_out           : bus output (right end of bus)
    o_drop_{ch}     : drop port of channel ch  (ch = 1 … 2*n_pairs)
    o_add_{ch}      : add  port of channel ch  (ch = 1 … 2*n_pairs)

    Key geometry (default parameters)
    ----------------------------------
    Bus length       = 2 × 15 + 6 × 35 = 240 µm
    Pair pitch       = 35 µm
    Same-side pitch  = 70 µm
    Ring footprint   = 16 µm
    Pair x-positions = 15, 50, 85, 120, 155, 190 µm  (within 240 µm bus)
    """
    c = gf.Component()

    bus_length = 2 * margin + n_pairs * ch_pitch  # 240 µm by default

    # ── Straight bus waveguide ─────────────────────────────────────────────────
    bus_ref = c << gf.components.straight(length=bus_length)
    bus_ref.move((0, 0))
    c.add_port("o_in",  port=bus_ref.ports["o1"])
    c.add_port("o_out", port=bus_ref.ports["o2"])

    # ── Ring unit template (above orientation) ─────────────────────────────────
    ring = gf.get_component(
        ring_unit,
        radius=ring_radius,
        length_x=ring_lx,
        length_y=ring_ly,
        gap=bus_gap,
    )

    # ── Place 6 bilateral pairs ────────────────────────────────────────────────
    #
    #   For each pair p (0 … n_pairs-1):
    #     - x_pair = margin + p × ch_pitch         (15, 50, 85, 120, 155, 190 µm)
    #     - odd  ch = 2p+1 → ring_double above bus (ring body at y > 0)
    #     - even ch = 2p+2 → ring_double below bus (ring body at y < 0,
    #                                                achieved by y-mirror)
    #
    for p in range(n_pairs):
        ch_odd  = 2 * p + 1   # 1, 3, 5, 7, 9, 11
        ch_even = 2 * p + 2   # 2, 4, 6, 8, 10, 12

        # x-position of this pair on the bus
        x_pair = margin + p * ch_pitch   # 15, 50, 85, 120, 155, 190 µm

        # ── Odd channel: ring ABOVE the bus ───────────────────────────────────
        r_above = c << ring
        # Centre the ring's bus coupling section at x_pair.
        # ring_double's bounding-box x-centre equals the midpoint of its bus
        # ports (o1.x, o2.x), so setting `.x` directly aligns the coupling
        # region (and ring body) symmetrically around x_pair.
        r_above.x = x_pair
        # ring_double already places its bus ports (o1, o2) at y = 0;
        # the ring body extends upward (y > 0) → no y-shift needed.

        # Expose add and drop ports for this channel.
        c.add_port(f"o_drop_{ch_odd}", port=r_above.ports["o4"])
        c.add_port(f"o_add_{ch_odd}",  port=r_above.ports["o3"])

        # ── Even channel: ring BELOW the bus ──────────────────────────────────
        r_below = c << ring
        # Mirror around the x-axis (y = 0): ring body moves to y < 0 while
        # bus ports (o1, o2) stay at y = 0 (they lie on the mirror axis).
        r_below.mirror((0, 0), (1, 0))
        # After mirroring, the bounding-box x-centre is unchanged (the mirror
        # is purely in y), so setting `.x` still aligns the coupling midpoint
        # with x_pair, exactly as for the above ring.
        r_below.x = x_pair

        c.add_port(f"o_drop_{ch_even}", port=r_below.ports["o4"])
        c.add_port(f"o_add_{ch_even}",  port=r_below.ports["o3"])

    return c


# ── Geometry helpers (exposed for testing) ────────────────────────────────────

def pair_x_positions(
    n_pairs: int = N_PAIRS,
    margin: float = MARGIN,
    ch_pitch: float = CH_PITCH,
) -> list:
    """Return the x-positions of all bilateral pairs.

    Returns
    -------
    list of float, length n_pairs
        Pair x-centres in µm: [margin + p × ch_pitch  for p in range(n_pairs)]
    """
    return [margin + p * ch_pitch for p in range(n_pairs)]


def bus_length(
    n_pairs: int = N_PAIRS,
    margin: float = MARGIN,
    ch_pitch: float = CH_PITCH,
) -> float:
    """Return the total bus length in µm (= 2 × margin + n_pairs × ch_pitch)."""
    return 2 * margin + n_pairs * ch_pitch


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    c = bilateral_ring_filter()
    gds_path = "ring_filter_bilateral.gds"
    c.write_gds(gds_path)
    print(f"GDS written → {gds_path}")
    print(f"  Bus length  : {bus_length():.1f} µm  (expected 240 µm)")
    print(f"  Pair x-pos  : {pair_x_positions()}")
    print(f"  Same-side Δ : {SAME_SIDE_PITCH:.1f} µm  (expected 70 µm)")
    print(f"  N channels  : {N_CH}")
    print(f"  N pairs     : {N_PAIRS}")
