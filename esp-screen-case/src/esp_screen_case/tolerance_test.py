"""Tolerance test piece — rail and channel sections to validate sliding fit.

Print this, snap the halves apart at the score line, and test the sliding fit.
If too tight: increase RAIL_CLEARANCE in dimensions.py
If too loose: decrease RAIL_CLEARANCE in dimensions.py
"""

from build123d import (
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Pos,
    Rectangle,
    extrude,
)

from esp_screen_case.dimensions import (
    CHANNEL_DEPTH,
    CHANNEL_WIDTH,
    RAIL_DEPTH,
    RAIL_WIDTH,
)

# Test piece dimensions
BASE_WIDTH = 30.0   # X: width of each half
BASE_DEPTH = 30.0   # Y: depth (rail slides along this axis)
BASE_HEIGHT = 5.0   # Z: base block height
SCORE_GAP = 0.4     # thin gap between halves for snapping apart


def build() -> Part:
    """Build rail + channel test piece as one printable part."""
    half_spacing = BASE_WIDTH / 2 + SCORE_GAP / 2

    with BuildPart() as piece:
        # --- Rail half (left side) ---
        with BuildPart(Pos(-half_spacing, 0, BASE_HEIGHT / 2), mode=Mode.ADD):
            Box(BASE_WIDTH, BASE_DEPTH, BASE_HEIGHT)

        # Rail protrusion on top of left half
        with BuildPart(
            Pos(-half_spacing, 0, BASE_HEIGHT + RAIL_DEPTH / 2), mode=Mode.ADD
        ):
            Box(RAIL_WIDTH, BASE_DEPTH, RAIL_DEPTH)

        # --- Channel half (right side) ---
        # Taller base to accommodate the channel cut
        channel_height = BASE_HEIGHT + CHANNEL_DEPTH
        with BuildPart(Pos(half_spacing, 0, channel_height / 2), mode=Mode.ADD):
            Box(BASE_WIDTH, BASE_DEPTH, channel_height)

        # Channel cut into top of right half
        with BuildPart(
            Pos(half_spacing, 0, channel_height - CHANNEL_DEPTH / 2), mode=Mode.SUBTRACT
        ):
            Box(CHANNEL_WIDTH, BASE_DEPTH + 1, CHANNEL_DEPTH + 0.1)

    return piece.part
