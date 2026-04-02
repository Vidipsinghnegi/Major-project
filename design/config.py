"""
Parametric DWDM demultiplexer configuration.

All physical units are in micrometres unless stated otherwise.
Wavelengths are in nanometres.
"""

# ---------------------------------------------------------------------------
# Waveguide platform (220-nm SOI strip)
# ---------------------------------------------------------------------------
WG_WIDTH   = 0.500   # um  — waveguide width
WG_HEIGHT  = 0.220   # um  — waveguide height (Si layer)
BOX_HEIGHT = 2.000   # um  — buried-oxide thickness
N_EFF      = 2.437   # effective index at 1550 nm
N_GROUP    = 4.182   # group index at 1550 nm

# ---------------------------------------------------------------------------
# Racetrack geometry (nominal — per-channel values are computed in dwdm_demux.py)
# ---------------------------------------------------------------------------
BEND_RADIUS    = 10.0   # um  — semicircle radius
COUPLING_LEN   = 15.0   # um  — straight coupling-section length (nominal)
GAP_BUS_RING   = 0.150  # um  — gap between bus and ring waveguide
GAP_RING_DROP  = 0.150  # um  — gap between ring and drop waveguide

# ---------------------------------------------------------------------------
# DWDM channel plan (ITU G.694.1, 100 GHz grid, C-band)
# ---------------------------------------------------------------------------
NUM_CHANNELS    = 8
FIRST_CHANNEL_NM = 1544.53   # nm  — ITU channel 35
CHANNEL_SPACING_NM = 0.8     # nm  ≈ 100 GHz at 1550 nm

# ---------------------------------------------------------------------------
# TiN microheater
# ---------------------------------------------------------------------------
HEATER_WIDTH   = 1.0    # um
HEATER_THICK   = 0.100  # um  (100 nm)
HEATER_OFFSET  = 1.0    # um  above waveguide top surface

# ---------------------------------------------------------------------------
# GDS layer definitions (generic 220-nm SOI PDK)
# ---------------------------------------------------------------------------
LAYER_WG     = (1, 0)    # silicon waveguide
LAYER_HEATER = (4, 0)    # TiN heater
LAYER_M1     = (31, 0)   # first metal (bond pads / routing)
LAYER_LABEL  = (66, 0)   # text labels

# ---------------------------------------------------------------------------
# Layout floor plan
# ---------------------------------------------------------------------------
CHANNEL_PITCH_Y  = 100.0   # um  — vertical pitch between racetracks
CHIP_MARGIN      = 50.0    # um  — margin from die edge
INPUT_BUS_LENGTH = 200.0   # um  — total length of input bus waveguide
