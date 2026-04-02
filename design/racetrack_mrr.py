"""
racetrack_mrr.py
================
gdsfactory component: thermally tunable racetrack microring resonator
with TiN microheater.

Usage (standalone)::

    python racetrack_mrr.py          # writes racetrack_mrr.gds to cwd

API::

    from racetrack_mrr import racetrack_mrr
    c = racetrack_mrr(bend_radius=10, coupling_len=15, gap=0.15)
    c.show()   # opens KLayout (if installed)
    c.write_gds("my_racetrack.gds")
"""

from __future__ import annotations

import gdsfactory as gf
from gdsfactory.typings import LayerSpec

from config import (
    WG_WIDTH,
    BEND_RADIUS,
    COUPLING_LEN,
    GAP_BUS_RING,
    GAP_RING_DROP,
    LAYER_WG,
    LAYER_HEATER,
    LAYER_LABEL,
    HEATER_WIDTH,
    HEATER_OFFSET,
)


@gf.cell
def racetrack_mrr(
    bend_radius: float = BEND_RADIUS,
    coupling_len: float = COUPLING_LEN,
    gap_bus: float = GAP_BUS_RING,
    gap_drop: float = GAP_RING_DROP,
    wg_width: float = WG_WIDTH,
    heater_width: float = HEATER_WIDTH,
    heater_offset: float = HEATER_OFFSET,
    layer_wg: LayerSpec = LAYER_WG,
    layer_heater: LayerSpec = LAYER_HEATER,
    layer_label: LayerSpec = LAYER_LABEL,
    channel_label: str = "ch0",
) -> gf.Component:
    """Racetrack MRR add-drop filter with TiN microheater.

    Parameters
    ----------
    bend_radius:   Semicircular bend radius [um].
    coupling_len:  Straight coupling section length [um] (both couplers).
    gap_bus:       Gap between bus waveguide and ring [um].
    gap_drop:      Gap between ring and drop waveguide [um].
    wg_width:      Waveguide width [um].
    heater_width:  TiN heater strip width [um].
    heater_offset: Vertical offset of heater above waveguide centre [um].
    layer_wg:      GDS layer for silicon waveguide.
    layer_heater:  GDS layer for TiN heater.
    layer_label:   GDS layer for text labels.
    channel_label: Text label for this channel.

    Returns
    -------
    gf.Component with ports: 'in', 'thru', 'drop', 'add'.
    """
    c = gf.Component()

    # ------------------------------------------------------------------
    # Geometry constants
    # ------------------------------------------------------------------
    dia = 2 * bend_radius

    # Total racetrack height (centre-to-centre of parallel straights):
    #   bus straight — gap_bus — wg_width — ring_width — ring_gap_inner
    # For simplicity, define the ring centre-to-bus offset:
    ring_to_bus = gap_bus + wg_width  # edge-to-edge gap + wg width

    # The ring consists of:
    #   - top straight (coupling section near bus)
    #   - bottom straight (coupling section near drop port)
    #   - two semicircular bends

    # ------------------------------------------------------------------
    # Bus waveguide (input → through)
    # ------------------------------------------------------------------
    bus_length = coupling_len + dia + 2 * bend_radius  # a bit wider
    bus = c << gf.components.straight(length=bus_length, width=wg_width,
                                       layer=layer_wg)
    bus.move((0, 0))

    # ------------------------------------------------------------------
    # Ring: top coupling straight
    # ------------------------------------------------------------------
    top_straight = c << gf.components.straight(
        length=coupling_len, width=wg_width, layer=layer_wg
    )
    top_y = -(ring_to_bus + wg_width / 2 + wg_width / 2)
    top_straight.move((bend_radius, top_y))

    # ------------------------------------------------------------------
    # Ring: semicircular bends
    # ------------------------------------------------------------------
    left_bend = c << gf.components.bend_circular(
        radius=bend_radius, angle=180, width=wg_width, layer=layer_wg
    )
    left_bend.connect("o1", top_straight.ports["o1"])

    right_bend = c << gf.components.bend_circular(
        radius=bend_radius, angle=180, width=wg_width, layer=layer_wg
    )
    right_bend.mirror_x()
    right_bend.connect("o1", top_straight.ports["o2"])

    # ------------------------------------------------------------------
    # Ring: bottom coupling straight
    # ------------------------------------------------------------------
    bot_straight = c << gf.components.straight(
        length=coupling_len, width=wg_width, layer=layer_wg
    )
    bot_straight.connect("o1", left_bend.ports["o2"])

    # ------------------------------------------------------------------
    # Drop waveguide
    # ------------------------------------------------------------------
    drop_y = bot_straight.ymin - gap_drop - wg_width / 2
    drop = c << gf.components.straight(
        length=bus_length, width=wg_width, layer=layer_wg
    )
    drop.move((0, drop_y - wg_width / 2))

    # ------------------------------------------------------------------
    # TiN heater (over top coupling section)
    # ------------------------------------------------------------------
    heater = c << gf.components.straight(
        length=coupling_len, width=heater_width, layer=layer_heater
    )
    heater.move(
        (top_straight.x - coupling_len / 2,
         top_y + heater_offset)
    )

    # ------------------------------------------------------------------
    # Port definitions
    # ------------------------------------------------------------------
    c.add_port("in",   port=bus.ports["o1"])
    c.add_port("thru", port=bus.ports["o2"])
    c.add_port("drop", port=drop.ports["o2"])
    c.add_port("add",  port=drop.ports["o1"])

    # ------------------------------------------------------------------
    # Label
    # ------------------------------------------------------------------
    c.add_label(
        text=channel_label,
        position=top_straight.center,
        layer=layer_label,
    )

    return c


# ---------------------------------------------------------------------------
# Standalone entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    component = racetrack_mrr(channel_label="ch1")
    component.show()
    component.write_gds("racetrack_mrr.gds")
    print("Written: racetrack_mrr.gds")
    print(f"  Ports: {list(component.ports.keys())}")
    print(f"  Bounding box: {component.bbox}")
