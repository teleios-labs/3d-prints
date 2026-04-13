"""Hidden wall bracket for CrowPanel 7" — mounts to drywall, shell slides on horizontally.

Design:
- Central hub with 4x screw holes for drywall anchors
- Two horizontal arms extending left and right (rail profile)
- Shell slides on from left side, snap detent locks at the right end
- Entire bracket hides behind the panel — invisible when mounted

Orientation: print flat (arms in XY plane), mount with arms horizontal.
The shell slides onto the arms from the left (entry side) and clicks
past the snap detent on the right (locking side).
"""

from build123d import (
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Pos,
    extrude,
)

from esp_screen_case.dimensions import (
    BRACKET_ARM_LENGTH,
    BRACKET_HUB_HEIGHT,
    BRACKET_HUB_WIDTH,
    BRACKET_THICKNESS,
    BRACKET_WALL,
    RAIL_DEPTH,
    RAIL_WIDTH,
    SCREW_HOLE_DIAMETER,
    SNAP_CATCH_LENGTH,
    SNAP_PROTRUSION,
)

# Derived
ARM_WIDTH = RAIL_WIDTH + 2 * BRACKET_WALL  # total arm width including walls around rail
SCREW_SPACING_X = BRACKET_HUB_WIDTH - 2 * BRACKET_WALL - SCREW_HOLE_DIAMETER
SCREW_SPACING_Y = BRACKET_HUB_HEIGHT - 2 * BRACKET_WALL - SCREW_HOLE_DIAMETER


def build() -> Part:
    """Build the wall bracket."""
    left_arm_x = -(BRACKET_HUB_WIDTH / 2 + BRACKET_ARM_LENGTH / 2)
    right_arm_x = BRACKET_HUB_WIDTH / 2 + BRACKET_ARM_LENGTH / 2
    rail_z = BRACKET_THICKNESS / 2 + RAIL_DEPTH / 2
    snap_x = right_arm_x + BRACKET_ARM_LENGTH / 2 - SNAP_CATCH_LENGTH / 2
    snap_z = BRACKET_THICKNESS / 2 + RAIL_DEPTH + SNAP_PROTRUSION / 2

    with BuildPart() as bracket:
        # Central hub (flat plate)
        Box(BRACKET_HUB_WIDTH, BRACKET_HUB_HEIGHT, BRACKET_THICKNESS)

        # Left + right arm bases
        with Locations(Pos(left_arm_x, 0, 0), Pos(right_arm_x, 0, 0)):
            Box(BRACKET_ARM_LENGTH, ARM_WIDTH, BRACKET_THICKNESS)

        # Raised rail profiles on top of each arm
        with Locations(Pos(left_arm_x, 0, rail_z), Pos(right_arm_x, 0, rail_z)):
            Box(BRACKET_ARM_LENGTH, RAIL_WIDTH, RAIL_DEPTH)

        # Snap detent on right arm tip
        with Locations(Pos(snap_x, 0, snap_z)):
            Box(SNAP_CATCH_LENGTH, RAIL_WIDTH, SNAP_PROTRUSION)

        # Screw holes through the hub
        screw_positions = [
            (SCREW_SPACING_X / 2, SCREW_SPACING_Y / 2),
            (-SCREW_SPACING_X / 2, SCREW_SPACING_Y / 2),
            (SCREW_SPACING_X / 2, -SCREW_SPACING_Y / 2),
            (-SCREW_SPACING_X / 2, -SCREW_SPACING_Y / 2),
        ]
        with BuildSketch(bracket.faces().sort_by(Axis.Z)[-1]):
            with Locations(screw_positions):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-BRACKET_THICKNESS, mode=Mode.SUBTRACT)

    return bracket.part
