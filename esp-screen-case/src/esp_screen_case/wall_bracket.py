"""Wall bracket with a vertical drop-in dovetail rail + solid shelf stop.

The bracket is a two-tier "T" profile:

    ┌──────────────┐  ← hub top (y = +HUB_Y/2)
    │              │  ← 8mm lead-in strip (top anchor hole lives here)
    │   ╱──────╲   │
    │  │        │  │
    │  │  rail  │  │  ← dovetail rail, 50mm long, sits on top of the upper hub
    │  │        │  │     front face, protrudes +Z toward the user
    │  │        │  │
    │   ╲──────╱   │
    │              │
 ┌──┴──────────────┴──┐  ← shelf top / rail bottom / upper-hub bottom
 │    SHELF FLANGE    │
 │       ● anchor     │  ← bottom anchor hole (centered in the flange)
 │                    │
 └────────────────────┘  ← hub bottom (y = -HUB_Y/2)

Upper hub: 30 × 58 × 4 mm (X × Y × Z). Contains the dovetail rail.
Shelf flange: 40 × 15 × 4 mm. 5mm wider than the upper hub on each
side, so the case's bottom edge has solid material to rest on outside
the bracket recess's X footprint (the case recess is 30mm wide, matching
the upper hub; the extra 5mm per side is the support zone).

Mount: 2× M3 drywall anchor holes through the hub. Top hole sits in the
8mm lead-in strip above the rail (cleared of the rail by 2mm). Bottom
hole is centered in the shelf flange.

Print orientation: flat on the bed, rail protruding +Z. Rail walls
print as near-vertical perimeters — no bridging, same strategy as
piece B in the tolerance test.

Assembly motion: case channel is open at its bottom edge. Lower the
case from above; the rail enters the channel, the dovetail undercut
captures it, and the case's bottom edge lands flat on the shelf
flange. Gravity alone retains it. No tools for attach or detach.
"""

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    extrude,
)

from esp_screen_case.cadlib import DovetailRail
from esp_screen_case.dimensions import (
    BRACKET_HUB_X,
    BRACKET_HUB_Y,
    BRACKET_HUB_Z,
    BRACKET_RAIL_LEAD_IN,
    BRACKET_RAIL_LENGTH,
    BRACKET_SHELF_X,
    BRACKET_SHELF_Y,
    RAIL_DEPTH,
    RAIL_TOP_WIDTH,
    RAIL_WIDTH,
    SCREW_HOLE_DIAMETER,
)


def build() -> Part:
    """Build the wall bracket."""
    # Y positions in the bracket's centered coordinate frame. Build from
    # the bottom up for clarity: hub bottom → shelf top → rail top → hub top.
    hub_bottom = -BRACKET_HUB_Y / 2
    shelf_top = hub_bottom + BRACKET_SHELF_Y
    rail_top = shelf_top + BRACKET_RAIL_LENGTH
    hub_top = rail_top + BRACKET_RAIL_LEAD_IN  # = +BRACKET_HUB_Y / 2

    # Box centers
    shelf_y_center = (hub_bottom + shelf_top) / 2
    upper_hub_y_center = (shelf_top + hub_top) / 2
    upper_hub_y_height = hub_top - shelf_top

    # Rail center (50mm tall, spans shelf_top → rail_top)
    rail_y_center = (shelf_top + rail_top) / 2

    # Anchor hole centers
    top_anchor_y = (rail_top + hub_top) / 2  # centered in the lead-in strip
    bot_anchor_y = shelf_y_center            # centered in the shelf flange

    with BuildPart() as bracket:
        # Shelf flange: wider than the upper hub, provides case-bottom support
        with Locations(Pos(0, shelf_y_center, BRACKET_HUB_Z / 2)):
            Box(BRACKET_SHELF_X, BRACKET_SHELF_Y, BRACKET_HUB_Z)

        # Upper hub: 30mm wide, holds the rail and the top anchor hole
        with Locations(Pos(0, upper_hub_y_center, BRACKET_HUB_Z / 2)):
            Box(BRACKET_HUB_X, upper_hub_y_height, BRACKET_HUB_Z)

        # Dovetail rail on the upper hub's front face, running along Y.
        # rotation=(0, 0, 90) rotates the DovetailRail's length axis from
        # X to Y; the narrow base lands at z=BRACKET_HUB_Z.
        with Locations(Pos(0, rail_y_center, BRACKET_HUB_Z)):
            DovetailRail(
                length=BRACKET_RAIL_LENGTH,
                base_width=RAIL_WIDTH,
                top_width=RAIL_TOP_WIDTH,
                height=RAIL_DEPTH,
                rotation=(0, 0, 90),
            )

        # M3 drywall anchor holes through the hub. The 0.1mm extra on
        # the extrude depth is an OCCT boolean-robustness overshoot so
        # the cut punches cleanly through the back face.
        with BuildSketch(Plane.XY.offset(BRACKET_HUB_Z)):
            with Locations(
                (0.0, top_anchor_y),
                (0.0, bot_anchor_y),
            ):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-BRACKET_HUB_Z - 0.1, mode=Mode.SUBTRACT)

    return bracket.part
