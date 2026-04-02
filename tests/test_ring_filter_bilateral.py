"""Tests for the bilateral 12-channel DWDM ring filter (design/ring_filter_bilateral.py).

Validated constraints (paper Table 3 and Fig. 5)
-------------------------------------------------
1.  Bus length = 2 × 15 + 6 × 35 = 240 µm
2.  Number of channel pairs = 6  (12 channels total)
3.  Pair pitch (consecutive) = 35 µm
4.  Same-side pitch = 2 × CH_PITCH = 70 µm
5.  Ring footprint = 2 × RING_RADIUS + RING_LX = 16 µm
6.  Each pair: odd channel ring ABOVE bus  (drop port y > 0)
7.  Each pair: even channel ring BELOW bus (drop port y < 0)
8.  Rings within a pair share the same x-position (bilateral alignment)
9.  Ports named o_drop_{ch} and o_add_{ch} for ch = 1 … 12
10. o_in and o_out ports on the bus ends
"""

import pytest
import gdsfactory as gf

gf.gpdk.PDK.activate()

from design.ring_filter_bilateral import (
    bilateral_ring_filter,
    ring_unit,
    bus_length,
    pair_x_positions,
    MARGIN,
    CH_PITCH,
    SAME_SIDE_PITCH,
    N_CH,
    N_PAIRS,
    RING_RADIUS,
    RING_LX,
    BUS_LENGTH,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def filter_component():
    """Build the bilateral ring filter once and reuse across tests."""
    return bilateral_ring_filter()


# ── 1. Module-level constants ──────────────────────────────────────────────────

class TestDesignParameters:
    def test_n_channels(self):
        assert N_CH == 12

    def test_n_pairs(self):
        assert N_PAIRS == 6

    def test_margin(self):
        assert MARGIN == pytest.approx(15.0)

    def test_ch_pitch(self):
        assert CH_PITCH == pytest.approx(35.0)

    def test_same_side_pitch_equals_twice_ch_pitch(self):
        assert SAME_SIDE_PITCH == pytest.approx(2 * CH_PITCH)

    def test_same_side_pitch_value(self):
        assert SAME_SIDE_PITCH == pytest.approx(70.0)

    def test_ring_footprint(self):
        """Ring footprint = Lc + 2R = 16 µm  (paper Table 3)."""
        footprint = RING_LX + 2 * RING_RADIUS
        assert footprint == pytest.approx(16.0)

    def test_bus_length_formula(self):
        assert BUS_LENGTH == pytest.approx(2 * MARGIN + N_PAIRS * CH_PITCH)

    def test_bus_length_value(self):
        assert BUS_LENGTH == pytest.approx(240.0)


# ── 2. Helper functions ────────────────────────────────────────────────────────

class TestHelpers:
    def test_bus_length_helper(self):
        assert bus_length() == pytest.approx(240.0)

    def test_bus_length_custom(self):
        assert bus_length(n_pairs=4, margin=10.0, ch_pitch=40.0) == pytest.approx(180.0)

    def test_pair_x_positions_count(self):
        xs = pair_x_positions()
        assert len(xs) == N_PAIRS

    def test_pair_x_positions_values(self):
        xs = pair_x_positions()
        expected = [MARGIN + p * CH_PITCH for p in range(N_PAIRS)]
        for x, ex in zip(xs, expected):
            assert x == pytest.approx(ex)

    def test_pair_x_positions_spacing(self):
        """Consecutive pair positions differ by CH_PITCH = 35 µm."""
        xs = pair_x_positions()
        for i in range(1, len(xs)):
            assert xs[i] - xs[i - 1] == pytest.approx(CH_PITCH)

    def test_pair_x_positions_custom(self):
        xs = pair_x_positions(n_pairs=3, margin=10.0, ch_pitch=20.0)
        assert xs == pytest.approx([10.0, 30.0, 50.0])


# ── 3. Ring unit component ─────────────────────────────────────────────────────

class TestRingUnit:
    def test_ring_unit_has_four_ports(self):
        ring = ring_unit()
        assert len(ring.ports) == 4

    def test_ring_unit_port_names(self):
        ring = ring_unit()
        names = {p.name for p in ring.ports}
        assert {"o1", "o2", "o3", "o4"} == names

    def test_ring_unit_bus_ports_at_y_zero(self):
        """Bus through-ports o1 and o2 must lie on y = 0."""
        ring = ring_unit()
        assert ring["o1"].center[1] == pytest.approx(0.0, abs=1e-3)
        assert ring["o2"].center[1] == pytest.approx(0.0, abs=1e-3)

    def test_ring_unit_drop_ports_above_bus(self):
        """Drop/add ports o3 and o4 must be above y = 0 (above-bus orientation)."""
        ring = ring_unit()
        assert ring["o3"].center[1] > 0
        assert ring["o4"].center[1] > 0


# ── 4. Top-level component: bus geometry ──────────────────────────────────────

class TestBusGeometry:
    def test_bus_length(self, filter_component):
        c = filter_component
        o_in  = c["o_in"]
        o_out = c["o_out"]
        measured = o_out.center[0] - o_in.center[0]
        assert measured == pytest.approx(240.0, abs=0.1)

    def test_bus_in_port_exists(self, filter_component):
        assert "o_in" in [p.name for p in filter_component.ports]

    def test_bus_out_port_exists(self, filter_component):
        assert "o_out" in [p.name for p in filter_component.ports]

    def test_bus_in_at_x_zero(self, filter_component):
        assert filter_component["o_in"].center[0] == pytest.approx(0.0, abs=0.1)

    def test_bus_out_at_bus_end(self, filter_component):
        c = filter_component
        assert c["o_out"].center[0] == pytest.approx(BUS_LENGTH, abs=0.1)

    def test_bus_runs_at_y_zero(self, filter_component):
        c = filter_component
        assert c["o_in"].center[1]  == pytest.approx(0.0, abs=0.5)
        assert c["o_out"].center[1] == pytest.approx(0.0, abs=0.5)


# ── 5. Port naming ─────────────────────────────────────────────────────────────

class TestPortNaming:
    def test_total_port_count(self, filter_component):
        """o_in + o_out + 12 drop + 12 add = 26 ports."""
        assert len(filter_component.ports) == 2 + 2 * N_CH

    def test_all_drop_ports_present(self, filter_component):
        port_names = {p.name for p in filter_component.ports}
        for ch in range(1, N_CH + 1):
            assert f"o_drop_{ch}" in port_names, f"missing o_drop_{ch}"

    def test_all_add_ports_present(self, filter_component):
        port_names = {p.name for p in filter_component.ports}
        for ch in range(1, N_CH + 1):
            assert f"o_add_{ch}" in port_names, f"missing o_add_{ch}"


# ── 6. Bilateral arrangement ───────────────────────────────────────────────────

class TestBilateralArrangement:
    def test_odd_channels_drop_above_bus(self, filter_component):
        """Drop ports of odd channels (above rings) must have y > 0."""
        c = filter_component
        for ch in range(1, N_CH + 1, 2):   # 1, 3, 5, 7, 9, 11
            y = c[f"o_drop_{ch}"].center[1]
            assert y > 0, f"R{ch} (odd/above) drop port y={y:.3f} must be > 0"

    def test_even_channels_drop_below_bus(self, filter_component):
        """Drop ports of even channels (below rings) must have y < 0."""
        c = filter_component
        for ch in range(2, N_CH + 1, 2):   # 2, 4, 6, 8, 10, 12
            y = c[f"o_drop_{ch}"].center[1]
            assert y < 0, f"R{ch} (even/below) drop port y={y:.3f} must be < 0"

    def test_odd_channels_add_above_bus(self, filter_component):
        """Add ports of odd channels (above rings) must have y > 0."""
        c = filter_component
        for ch in range(1, N_CH + 1, 2):
            y = c[f"o_add_{ch}"].center[1]
            assert y > 0, f"R{ch} (odd/above) add port y={y:.3f} must be > 0"

    def test_even_channels_add_below_bus(self, filter_component):
        """Add ports of even channels (below rings) must have y < 0."""
        c = filter_component
        for ch in range(2, N_CH + 1, 2):
            y = c[f"o_add_{ch}"].center[1]
            assert y < 0, f"R{ch} (even/below) add port y={y:.3f} must be < 0"

    @pytest.mark.parametrize("pair_idx", range(N_PAIRS))
    def test_pair_x_alignment(self, filter_component, pair_idx):
        """Above and below rings of each pair share the same x-position."""
        c = filter_component
        p = pair_idx
        ch_odd  = 2 * p + 1
        ch_even = 2 * p + 2

        # Use midpoint of drop and add ports as ring x-centre proxy.
        above_drop_x = c[f"o_drop_{ch_odd}"].center[0]
        above_add_x  = c[f"o_add_{ch_odd}"].center[0]
        below_drop_x = c[f"o_drop_{ch_even}"].center[0]
        below_add_x  = c[f"o_add_{ch_even}"].center[0]

        above_cx = (above_drop_x + above_add_x) / 2
        below_cx = (below_drop_x + below_add_x) / 2

        assert above_cx == pytest.approx(below_cx, abs=0.1), (
            f"Pair {p}: above ring x={above_cx:.2f} µm ≠ "
            f"below ring x={below_cx:.2f} µm (expected same)"
        )

    @pytest.mark.parametrize("pair_idx", range(N_PAIRS))
    def test_pair_x_position(self, filter_component, pair_idx):
        """Each pair's x-centre equals MARGIN + p × CH_PITCH."""
        c = filter_component
        p = pair_idx
        ch_odd = 2 * p + 1
        expected_x = MARGIN + p * CH_PITCH

        drop_x = c[f"o_drop_{ch_odd}"].center[0]
        add_x  = c[f"o_add_{ch_odd}"].center[0]
        actual_x = (drop_x + add_x) / 2

        assert actual_x == pytest.approx(expected_x, abs=1.0), (
            f"Pair {p}: x={actual_x:.2f} µm, expected {expected_x:.2f} µm"
        )

    def test_above_ring_x_spacing(self, filter_component):
        """Consecutive above-ring x-centres differ by CH_PITCH = 35 µm."""
        c = filter_component
        xs = []
        for p in range(N_PAIRS):
            ch_odd = 2 * p + 1
            drop_x = c[f"o_drop_{ch_odd}"].center[0]
            add_x  = c[f"o_add_{ch_odd}"].center[0]
            xs.append((drop_x + add_x) / 2)

        for i in range(1, len(xs)):
            spacing = xs[i] - xs[i - 1]
            assert spacing == pytest.approx(CH_PITCH, abs=0.1), (
                f"Same-side spacing R{2*(i-1)+1}→R{2*i+1}: "
                f"{spacing:.2f} µm ≠ {CH_PITCH} µm"
            )

    def test_below_ring_x_spacing(self, filter_component):
        """Consecutive below-ring x-centres differ by CH_PITCH = 35 µm."""
        c = filter_component
        xs = []
        for p in range(N_PAIRS):
            ch_even = 2 * p + 2
            drop_x = c[f"o_drop_{ch_even}"].center[0]
            add_x  = c[f"o_add_{ch_even}"].center[0]
            xs.append((drop_x + add_x) / 2)

        for i in range(1, len(xs)):
            spacing = xs[i] - xs[i - 1]
            assert spacing == pytest.approx(CH_PITCH, abs=0.1), (
                f"Same-side spacing R{2*(i-1)+2}→R{2*i+2}: "
                f"{spacing:.2f} µm ≠ {CH_PITCH} µm"
            )


# ── 7. Custom-parameter smoke test ────────────────────────────────────────────

class TestCustomParameters:
    def test_custom_4_pairs(self):
        """4-pair filter: bus = 2×10 + 4×30 = 140 µm."""
        c = bilateral_ring_filter(n_pairs=4, margin=10.0, ch_pitch=30.0)
        o_in  = c["o_in"]
        o_out = c["o_out"]
        assert o_out.center[0] - o_in.center[0] == pytest.approx(140.0, abs=0.1)

    def test_custom_2_pairs_bilateral(self):
        """2-pair filter: R1 above, R2 below, R3 above, R4 below."""
        c = bilateral_ring_filter(n_pairs=2, margin=10.0, ch_pitch=40.0)
        # Odd channels → above
        for ch in [1, 3]:
            assert c[f"o_drop_{ch}"].center[1] > 0
        # Even channels → below
        for ch in [2, 4]:
            assert c[f"o_drop_{ch}"].center[1] < 0
