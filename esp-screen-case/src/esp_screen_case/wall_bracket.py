"""Wall bracket with a vertical drop-in dovetail rail + solid shelf stop.

Geometry overview (front view, user facing the wall):

    ┌─────────────┐  ← top of hub (y = +HUB_Y/2)
    │   ╱─────╲   │
    │  │ rail  │  │  ← dovetail rail, 50mm long, sits on top of the hub
    │  │  ...  │  │     front face, protrudes +Z toward the user
    │   ╲─────╱   │
    ├─────────────┤  ← rail bottom / shelf top
    │   SOLID     │
    │   SHELF     │  ← bottom 15mm of hub, solid face
    └─────────────┘  ← bottom of hub (y = -HUB_Y/2)

Mount: 2× M3 drywall anchor holes through the hub. Top hole sits in
the 2mm lead-in strip above the rail; bottom hole is centered in the
shelf.

Print orientation: flat on the bed, rail protruding +Z. Rail walls
print as near-vertical perimeters — no bridging, same strategy as
piece B in the tolerance test.

Assembly motion: case channel is open at its bottom edge. Lower the
case from above; the rail enters the channel, the dovetail undercut
captures it, and the case's bottom edge lands flat on the shelf.
Gravity alone retains it. No tools for attach or detach.
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
    BRACKET_SHELF_Y,
    RAIL_DEPTH,
    RAIL_TOP_WIDTH,
    RAIL_WIDTH,
    SCREW_HOLE_DIAMETER,
)


def build() -> Part:
    """Build the wall bracket."""
    # Rail occupies the top portion of the hub with a 2mm lead-in strip
    # above it and a 15mm shelf below it.
    rail_y_max = BRACKET_HUB_Y / 2 - BRACKET_RAIL_LEAD_IN
    rail_y_min = rail_y_max - BRACKET_RAIL_LENGTH
    rail_y_center = (rail_y_max + rail_y_min) / 2

    # Anchor hole Y positions: top hole in the lead-in strip, bottom
    # hole centered in the shelf.
    top_anchor_y = BRACKET_HUB_Y / 2 - BRACKET_RAIL_LEAD_IN / 2
    bot_anchor_y = -BRACKET_HUB_Y / 2 + BRACKET_SHELF_Y / 2

    with BuildPart() as bracket:
        # Hub: centered in X and Y at the origin. Z = 0 at the wall face,
        # Z = BRACKET_HUB_Z at the hub front face.
        with Locations(Pos(0, 0, BRACKET_HUB_Z / 2)):
            Box(BRACKET_HUB_X, BRACKET_HUB_Y, BRACKET_HUB_Z)

        # Dovetail rail sitting on the hub front face, running along Y.
        # rotation=(0, 0, 90) rotates the DovetailRail's length axis
        # from X to Y; the narrow base lands at z=BRACKET_HUB_Z.
        with Locations(Pos(0, rail_y_center, BRACKET_HUB_Z)):
            DovetailRail(
                length=BRACKET_RAIL_LENGTH,
                base_width=RAIL_WIDTH,
                top_width=RAIL_TOP_WIDTH,
                height=RAIL_DEPTH,
                rotation=(0, 0, 90),
            )

        # M3 drywall anchor holes through the hub.
        with BuildSketch(Plane.XY.offset(BRACKET_HUB_Z)):
            with Locations(
                (0.0, top_anchor_y),
                (0.0, bot_anchor_y),
            ):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-BRACKET_HUB_Z - 0.1, mode=Mode.SUBTRACT)

    return bracket.part
