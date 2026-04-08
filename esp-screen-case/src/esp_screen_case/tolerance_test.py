"""Tolerance test piece — dovetail rail and channel that slide together.

Two pieces printed side by side, snap apart at the score line:
- Piece A: flat plate with a dovetail rail (wide base, narrow top)
- Piece B: block with matching dovetail channel, open at -X end (entry)

Both sit flat on the table. Place B over A, slide along +X toward the closed end.
Snap bump near the closed end clicks into a pocket to lock.

Cross-section (looking at the open entry end):

Piece A (rail):              Piece B (channel):
    ╲━━━━╱  narrow top       ┌──╱      ╲──┐
     ╲  ╱                    │ ╱        ╲ │
      ╲╱    wide base        │╱ dovetail ╲│
──────────────               └────────────┘
│   base plate  │

Slide direction: -X (open entry) ──────► +X (end stop + snap click)
"""

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Polygon,
    Pos,
    Wedge,
    extrude,
)

from esp_screen_case.dimensions import (
    RAIL_DEPTH,
    RAIL_WIDTH,
    SNAP_CATCH_LENGTH,
    SNAP_POCKET_EXTRA,
    SNAP_POCKET_RAMP,
    SNAP_PROTRUSION,
    SNAP_RAMP_LENGTH,
)

# Test piece sizing
LENGTH = 60.0
BASE_WIDTH = 30.0
BASE_THICK = 3.0

# Dovetail rail — narrow at base, wider at top (gravity locks the screen on)
DOVE_BASE = RAIL_WIDTH - 1.0   # 9mm base (narrow)
DOVE_TOP = RAIL_WIDTH + 1.0    # 11mm top (wide) — subtle 1mm/side taper
DOVE_HT = RAIL_DEPTH           # 7mm

# Channel clearance
CLEARANCE = 0.2
CHAN_BASE = DOVE_BASE + 2 * CLEARANCE
CHAN_TOP = DOVE_TOP + 2 * CLEARANCE
CHAN_HT = DOVE_HT + 0.3

# Frame — tall enough for channel + snap bump recess above it
FRAME_WIDTH = DOVE_BASE + 10.0
FRAME_HT = BASE_THICK + CHAN_HT + SNAP_PROTRUSION + 0.5  # room for bump pocket above channel

SCORE_GAP = 0.5
END_WALL = 2.0

# Snap position: the bump is 3mm from the +X end of the rail.
# The end wall must be positioned so the rail tip hits it exactly when
# the bump is aligned with the pocket. Rail tip = LENGTH/2 = 30mm.
# Bump center = LENGTH/2 - SNAP_CATCH_LENGTH/2 - 3.0 = 26mm from center.
# When assembled, rail slides in from -X. Rail tip reaches the end wall.
# End wall position from center = LENGTH/2 - END_WALL/2 = 29mm.
# So bump at X=26 is 3mm before the end wall. Pocket must be at the same X=26.
SNAP_X = LENGTH / 2 - SNAP_CATCH_LENGTH / 2 - 3.0


def build() -> Part:
    """Build dovetail slide test with snap detent."""
    piece_offset = max(BASE_WIDTH, FRAME_WIDTH) / 2 + SCORE_GAP / 2
    taper = (DOVE_TOP - DOVE_BASE) / 2  # positive: how much wider the top is per side

    with BuildPart() as result:
        # ============================================
        # PIECE A — dovetail rail on flat plate
        # Narrow base, wider top — gravity locks screen on
        # ============================================

        # Base plate
        with BuildPart(Pos(0, -piece_offset, BASE_THICK / 2), mode=Mode.ADD):
            Box(LENGTH, BASE_WIDTH, BASE_THICK)

        # Rail: start as DOVE_TOP wide box (the wider dimension)
        with BuildPart(
            Pos(0, -piece_offset, BASE_THICK + DOVE_HT / 2), mode=Mode.ADD
        ):
            Box(LENGTH, DOVE_TOP, DOVE_HT)

        # Cut triangular wedges from BOTTOM corners to narrow the base
        # At Z=BASE_THICK (bottom): cut taper mm. At Z=BASE_THICK+DOVE_HT (top): no cut.
        for y_sign in [-1, 1]:
            outer_y = -piece_offset + y_sign * DOVE_TOP / 2
            with BuildSketch(Plane.YZ.offset(-LENGTH / 2 - 0.5)):
                if y_sign == -1:
                    # Left: triangle removing bottom-left corner
                    Polygon(
                        [
                            (outer_y - 0.1, BASE_THICK - 0.1),  # bottom outer
                            (outer_y + taper, BASE_THICK - 0.1),  # bottom inner
                            (outer_y - 0.1, BASE_THICK + DOVE_HT + 0.1),  # top outer (no cut)
                        ],
                        align=None,
                    )
                else:
                    # Right: triangle removing bottom-right corner
                    Polygon(
                        [
                            (outer_y - taper, BASE_THICK - 0.1),  # bottom inner
                            (outer_y + 0.1, BASE_THICK - 0.1),  # bottom outer
                            (outer_y + 0.1, BASE_THICK + DOVE_HT + 0.1),  # top outer (no cut)
                        ],
                        align=None,
                    )
            extrude(amount=LENGTH + 1, mode=Mode.SUBTRACT)

        # Snap bump on rail: small bump with entry ramp
        #
        # Side view (sliding →):
        #                   ┌──┐
        #              ╱╱╱╱╱│  │  <- SNAP_PROTRUSION (1mm)
        # ━━━━━━━━━━━━╱ramp │  │━━━━|
        #                    catch
        #
        # The bump slides in a groove in the channel ceiling, then drops
        # into a deeper pocket at the end for the snap click.

        rail_top_z = BASE_THICK + DOVE_HT
        bump_width = DOVE_TOP - 1.0
        ramp_x_end = SNAP_X - SNAP_CATCH_LENGTH / 2
        ramp_x_start = ramp_x_end - SNAP_RAMP_LENGTH

        # Entry ramp: triangle on XZ plane, extruded across the rail width
        ramp_offset = piece_offset - bump_width / 2 - 0.1
        with BuildSketch(Plane.XZ.offset(ramp_offset)):
            Polygon(
                [
                    (ramp_x_start, rail_top_z),                    # ramp start flush
                    (ramp_x_end, rail_top_z),                      # ramp end base
                    (ramp_x_end, rail_top_z + SNAP_PROTRUSION),    # ramp end peak
                ],
                align=None,
            )
        extrude(amount=bump_width + 0.2, mode=Mode.ADD)

        # Catch: flat block at full bump height
        with BuildPart(
            Pos(SNAP_X, -piece_offset, rail_top_z + SNAP_PROTRUSION / 2),
            mode=Mode.ADD,
        ):
            Box(SNAP_CATCH_LENGTH, bump_width, SNAP_PROTRUSION)

        # ============================================
        # PIECE B — dovetail channel
        # Open at -X end, end wall at +X end
        # ============================================

        # Solid frame
        with BuildPart(Pos(0, piece_offset, FRAME_HT / 2), mode=Mode.ADD):
            Box(LENGTH, FRAME_WIDTH, FRAME_HT)

        # Cut dovetail channel — full length through to +X end
        # Then we'll add an end wall with the dovetail profile cut into it
        with BuildPart(
            Pos(0, piece_offset, CHAN_HT / 2), mode=Mode.SUBTRACT
        ):
            Box(LENGTH + 1, CHAN_BASE, CHAN_HT + 0.1)

        # Widen channel at ceiling to CHAN_TOP by cutting triangular strips
        chan_taper = (CHAN_TOP - CHAN_BASE) / 2
        for y_sign in [-1, 1]:
            side_y = piece_offset + y_sign * CHAN_BASE / 2
            with BuildSketch(Plane.YZ.offset(-LENGTH / 2 - 0.5)):
                if y_sign == -1:
                    Polygon(
                        [
                            (side_y - chan_taper - 0.1, CHAN_HT + 0.1),
                            (side_y, CHAN_HT + 0.1),
                            (side_y, -0.1),
                        ],
                        align=None,
                    )
                else:
                    Polygon(
                        [
                            (side_y, CHAN_HT + 0.1),
                            (side_y + chan_taper + 0.1, CHAN_HT + 0.1),
                            (side_y, -0.1),
                        ],
                        align=None,
                    )
            extrude(amount=LENGTH + 1, mode=Mode.SUBTRACT)

        # Add end wall at +X with dovetail-shaped opening
        # Solid wall first, then cut the dovetail profile through it
        end_wall_x = LENGTH / 2 - END_WALL / 2
        with BuildPart(
            Pos(end_wall_x, piece_offset, FRAME_HT / 2), mode=Mode.ADD
        ):
            Box(END_WALL, FRAME_WIDTH, FRAME_HT)

        # Cut dovetail opening through the end wall (matches rail profile + clearance)
        with BuildPart(
            Pos(end_wall_x, piece_offset, CHAN_HT / 2), mode=Mode.SUBTRACT
        ):
            Box(END_WALL + 1, CHAN_BASE, CHAN_HT + 0.1)

        # Taper the end wall opening to match channel
        for y_sign in [-1, 1]:
            side_y = piece_offset + y_sign * CHAN_BASE / 2
            with BuildSketch(Plane.YZ.offset(end_wall_x - END_WALL / 2 - 0.5)):
                if y_sign == -1:
                    Polygon(
                        [
                            (side_y - chan_taper - 0.1, CHAN_HT + 0.1),
                            (side_y, CHAN_HT + 0.1),
                            (side_y, -0.1),
                        ],
                        align=None,
                    )
                else:
                    Polygon(
                        [
                            (side_y, CHAN_HT + 0.1),
                            (side_y + chan_taper + 0.1, CHAN_HT + 0.1),
                            (side_y, -0.1),
                        ],
                        align=None,
                    )
            extrude(amount=END_WALL + 1, mode=Mode.SUBTRACT)

        # Bump groove in channel ceiling — runs full X length at bump Y position
        # This gives the bump a slot to slide through without hitting the ceiling
        groove_depth = SNAP_PROTRUSION + 0.1  # slight clearance above bump
        groove_width = bump_width + 0.4
        with BuildPart(
            Pos(0, piece_offset, CHAN_HT + groove_depth / 2),
            mode=Mode.SUBTRACT,
        ):
            Box(LENGTH + 2, groove_width, groove_depth)

        # Snap pocket — deeper recess at snap position with ramps on both sides
        # The pocket is SNAP_POCKET_EXTRA deeper than the groove, so when the bump
        # enters the pocket, the channel can drop slightly into the deeper recess.
        #
        # Cross-section along X (sliding →):
        #                                              ╱ ramp    ramp ╲
        # ━━━groove━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╱              ╲━━━
        #                                              pocket (deeper)
        pocket_total_len = SNAP_CATCH_LENGTH + 2 * SNAP_POCKET_RAMP
        pocket_z_top = CHAN_HT + groove_depth + SNAP_POCKET_EXTRA  # deeper than groove

        # Main pocket recess (deeper portion, full width of ramp + catch)
        with BuildPart(
            Pos(
                SNAP_X,
                piece_offset,
                CHAN_HT + groove_depth + SNAP_POCKET_EXTRA / 2,
            ),
            mode=Mode.SUBTRACT,
        ):
            Box(pocket_total_len, groove_width, SNAP_POCKET_EXTRA + 0.1)

        # Entry ramp (-X side of pocket) — trapezoidal cut transitioning
        # from groove depth to pocket depth over SNAP_POCKET_RAMP length
        pocket_entry_x_end = SNAP_X - (SNAP_CATCH_LENGTH / 2 + SNAP_POCKET_RAMP)
        pocket_entry_x_start = SNAP_X - SNAP_CATCH_LENGTH / 2

        # Exit ramp (+X side of pocket)
        pocket_exit_x_start = SNAP_X + SNAP_CATCH_LENGTH / 2
        pocket_exit_x_end = SNAP_X + (SNAP_CATCH_LENGTH / 2 + SNAP_POCKET_RAMP)

        # Build ramps as triangular XZ-plane cuts extruded across groove width
        pocket_ramp_offset = -piece_offset - groove_width / 2 - 0.1
        # Note: we're in piece B area now, so +Y side; need offset in -Y direction
        # Plane.XZ.offset(v) places plane at Y=-v, so we want v = -(piece_offset + w/2 + 0.1)
        pocket_ramp_offset = -(piece_offset + groove_width / 2 + 0.1)

        # -X ramp: material fills from groove level up to pocket depth as we move -X
        # i.e., subtract triangle that's deepest at pocket side, zero at groove side
        with BuildSketch(Plane.XZ.offset(pocket_ramp_offset)):
            Polygon(
                [
                    (pocket_entry_x_end, CHAN_HT + groove_depth - 0.05),        # groove level at far -X
                    (pocket_entry_x_start, CHAN_HT + groove_depth - 0.05),      # groove level at pocket edge
                    (pocket_entry_x_start, CHAN_HT + groove_depth + SNAP_POCKET_EXTRA + 0.1),  # pocket depth at pocket edge
                ],
                align=None,
            )
        extrude(amount=groove_width + 0.2, mode=Mode.SUBTRACT)

        # +X ramp: mirror of -X ramp
        with BuildSketch(Plane.XZ.offset(pocket_ramp_offset)):
            Polygon(
                [
                    (pocket_exit_x_start, CHAN_HT + groove_depth - 0.05),       # pocket edge at groove level
                    (pocket_exit_x_end, CHAN_HT + groove_depth - 0.05),         # far +X at groove level
                    (pocket_exit_x_start, CHAN_HT + groove_depth + SNAP_POCKET_EXTRA + 0.1),  # pocket depth at pocket edge
                ],
                align=None,
            )
        extrude(amount=groove_width + 0.2, mode=Mode.SUBTRACT)

    return result.part
