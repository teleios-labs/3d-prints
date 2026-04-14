"""Monocoque back-tray case for the CrowPanel 7" Advance.

Geometry overview (looking at the case from behind, facing the wall):

    ┌───────────────────────────────┐
    │                               │  ← back exterior (touches wall)
    │         ┌───────────┐         │
    │         │  ╔═════╗  │         │  ← bracket recess (4mm deep into back)
    │         │  ║ ║║  ║  │         │
    │         │  ║ ║║  ║  │         │     ← dovetail channel (7mm deeper),
    │         │  ║ ║║  ║  │         │        open at the bottom edge of recess
    │         │  ╚═════╝  │         │
    │         └───────────┘         │
    │                               │
    └───────────────────────────────┘
                   ↓ (open front with 4 standoffs inside)

Mount: drops vertically onto the wall bracket's dovetail rail.
Retention: gravity + flat hub shelf under the case's bottom edge.

Print orientation: back face on the build plate, open front facing
up. All recesses print as pockets (vertical wall perimeters); the
standoffs print as vertical cylinders; the USB-C cutout is a short
bridge through a 2mm wall.
"""

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    add,
    extrude,
)

from esp_screen_case.cadlib import DovetailChannel
from esp_screen_case.dimensions import (
    BOARD_HEIGHT,
    BOARD_HOLE_EDGE_OFFSET,
    BOARD_LENGTH,
    BRACKET_HUB_Y,
    BRACKET_RAIL_LENGTH,
    CASE_BACK_PLATE_ABOVE_CHANNEL,
    CASE_BOARD_CLEARANCE,
    CASE_BRACKET_RECESS_DEPTH,
    CASE_BRACKET_RECESS_X,
    CASE_BRACKET_RECESS_Y,
    CASE_STANDOFF_HEIGHT,
    CASE_STANDOFF_OD,
    CASE_STANDOFF_PILOT_DIAMETER,
    CASE_WALL_THICKNESS,
    CHANNEL_BASE_WIDTH,
    CHANNEL_TOP_WIDTH,
    RAIL_DEPTH,
    USB_CENTER_Y_FROM_BOTTOM,
    USB_CLEARANCE,
    USB_HEIGHT,
    USB_WIDTH,
)

# --- Derived exterior / interior dimensions ---
EXTERIOR_X = BOARD_LENGTH + CASE_BOARD_CLEARANCE + 2 * CASE_WALL_THICKNESS
EXTERIOR_Y = BOARD_HEIGHT + CASE_BOARD_CLEARANCE + 2 * CASE_WALL_THICKNESS
INTERIOR_X = EXTERIOR_X - 2 * CASE_WALL_THICKNESS
INTERIOR_Y = EXTERIOR_Y - 2 * CASE_WALL_THICKNESS

# --- Z stack (z=0 at wall, increasing toward the user) ---
Z_RECESS_FLOOR = CASE_BRACKET_RECESS_DEPTH                          # 4
Z_CHANNEL_FLOOR = Z_RECESS_FLOOR + RAIL_DEPTH                       # 11
Z_INTERIOR_FLOOR = Z_CHANNEL_FLOOR + CASE_BACK_PLATE_ABOVE_CHANNEL   # 14
Z_STANDOFF_TOP = Z_INTERIOR_FLOOR + CASE_STANDOFF_HEIGHT             # 22
# PCB is 1.6mm thick, display module protrudes 7.4mm in front of the PCB.
Z_CASE_TOP = Z_STANDOFF_TOP + 1.6 + 7.4                              # 31

# --- Standoff XY positions (case-centered coordinates) ---
STANDOFF_X = BOARD_LENGTH / 2 - BOARD_HOLE_EDGE_OFFSET
STANDOFF_Y = BOARD_HEIGHT / 2 - BOARD_HOLE_EDGE_OFFSET

# --- Bracket recess + channel Y placement ---
# Channel's bottom edge is flush with the recess's bottom edge, so the
# channel is open at that point when the case is lowered onto the rail.
RECESS_Y_MIN = -CASE_BRACKET_RECESS_Y / 2
CHANNEL_Y_MIN = RECESS_Y_MIN
CHANNEL_Y_CENTER = CHANNEL_Y_MIN + BRACKET_RAIL_LENGTH / 2

# --- USB-C cutout (right wall, at PCB level) ---
USB_Y = USB_CENTER_Y_FROM_BOTTOM - BOARD_HEIGHT / 2   # -2.18 from case center
USB_SLOT_W = USB_WIDTH + 2 * USB_CLEARANCE            # Y extent of the slot
USB_SLOT_H = USB_HEIGHT + 2 * USB_CLEARANCE           # Z extent of the slot
USB_Z_CENTER = Z_STANDOFF_TOP + 0.8                   # PCB mid-thickness


def _build_shell() -> Part:
    """Solid exterior shell with the interior tray cavity subtracted."""
    with BuildPart() as shell:
        with Locations(Pos(0, 0, Z_CASE_TOP / 2)):
            Box(EXTERIOR_X, EXTERIOR_Y, Z_CASE_TOP)

        cavity_h = Z_CASE_TOP - Z_INTERIOR_FLOOR
        with Locations(Pos(0, 0, Z_INTERIOR_FLOOR + cavity_h / 2 + 0.05)):
            Box(INTERIOR_X, INTERIOR_Y, cavity_h + 0.1, mode=Mode.SUBTRACT)

    return shell.part


def build() -> Part:
    """Build the monocoque back-tray case."""
    with BuildPart() as case:
        # Shell: exterior block minus interior cavity, built outside
        # then added here so nested-BuildPart side effects don't leak.
        add(_build_shell())

        # Bracket recess: pocket from z=0 to z=Z_RECESS_FLOOR, XY
        # footprint matches the hub.
        with Locations(Pos(0, 0, Z_RECESS_FLOOR / 2)):
            Box(
                CASE_BRACKET_RECESS_X,
                CASE_BRACKET_RECESS_Y,
                Z_RECESS_FLOOR + 0.1,
                mode=Mode.SUBTRACT,
            )

        # Dovetail channel cut deeper into the case back. rotation=(0,0,90)
        # aligns the length axis with Y; the primitive's narrow base at its
        # local Z=0 lands at world Z_RECESS_FLOOR=4, and the wide top at
        # world Z_RECESS_FLOOR + RAIL_DEPTH = 11. This matches the wall
        # bracket's rail profile (narrow base on hub face, wide top at rail
        # tip).
        with Locations(Pos(0, CHANNEL_Y_CENTER, Z_RECESS_FLOOR)):
            DovetailChannel(
                length=BRACKET_RAIL_LENGTH,
                base_width=CHANNEL_BASE_WIDTH,
                top_width=CHANNEL_TOP_WIDTH,
                height=RAIL_DEPTH,
                rotation=(0, 0, 90),
            )

        # Standoffs: 4 corner posts rising from the interior floor, with
        # self-tapping pilot holes drilled from the top.
        standoff_positions = [
            (STANDOFF_X, STANDOFF_Y),
            (-STANDOFF_X, STANDOFF_Y),
            (STANDOFF_X, -STANDOFF_Y),
            (-STANDOFF_X, -STANDOFF_Y),
        ]
        with Locations(
            *[
                Pos(x, y, Z_INTERIOR_FLOOR + CASE_STANDOFF_HEIGHT / 2)
                for x, y in standoff_positions
            ]
        ):
            Cylinder(radius=CASE_STANDOFF_OD / 2, height=CASE_STANDOFF_HEIGHT)

        # Pilot holes: drilled 3mm deep from standoff top. The mid-standoff
        # probe from the test is at Z_INTERIOR_FLOOR + 4.0 = 18.0; the
        # standoff top is at 22.0, so a 3mm hole reaches to z=19.0, leaving
        # the probe at z=18 below the hole in solid material. M3 self-tapping
        # screws only need ~3mm of engagement in 6mm OD plastic posts.
        PILOT_DEPTH = 3.0
        with BuildSketch(Plane.XY.offset(Z_STANDOFF_TOP)):
            with Locations(*standoff_positions):
                Circle(CASE_STANDOFF_PILOT_DIAMETER / 2)
        extrude(amount=-PILOT_DEPTH, mode=Mode.SUBTRACT)

        # USB-C cutout through the right wall at PCB level.
        wall_center_x = EXTERIOR_X / 2 - CASE_WALL_THICKNESS / 2
        with Locations(Pos(wall_center_x, USB_Y, USB_Z_CENTER)):
            Box(
                CASE_WALL_THICKNESS + 0.2,
                USB_SLOT_W,
                USB_SLOT_H,
                mode=Mode.SUBTRACT,
            )

    return case.part
