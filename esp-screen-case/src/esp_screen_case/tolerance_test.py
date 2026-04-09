"""Tolerance test piece — dovetail rail and channel that slide together.

Two pieces printed side by side, snap apart at the score line:
- Piece A: flat plate with a dovetail rail (narrow base, wider top)
- Piece B: block with matching dovetail channel, open at -X end (entry)

Both sit flat on the table. Place B over A, slide along +X toward the
closed end. Snap bump near the closed end clicks into a pocket to lock.

Cross-section (looking at the open entry end):

Piece A (rail):              Piece B (channel):
    ╲━━━━╱  wider top         ┌──╱      ╲──┐
     ╲  ╱                     │ ╱        ╲ │
      ╲╱    narrow base       │╱ dovetail ╲│
──────────────                └────────────┘
│   base plate  │

Slide direction: -X (open entry) ──────► +X (end stop + snap click)
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

from esp_screen_case.cadlib import (
    DovetailChannel,
    DovetailRail,
    SnapBump,
    SnapPocket,
)
from esp_screen_case.dimensions import (
    RAIL_DEPTH,
    RAIL_WIDTH,
    SCREW_HOLE_DIAMETER,
    SNAP_CATCH_LENGTH,
    SNAP_POCKET_EXTRA,
    SNAP_POCKET_RAMP,
    SNAP_PROTRUSION,
    SNAP_RAMP_LENGTH,
)

# --- Test piece sizing ---
LENGTH = 60.0
BASE_WIDTH = 30.0
BASE_THICK = 3.0

# --- Dovetail rail ---
# Narrow at base, wider at top — gravity locks the screen on
DOVE_BASE = RAIL_WIDTH - 1.0   # 9mm base (narrow)
DOVE_TOP = RAIL_WIDTH + 1.0    # 11mm top (wide) — subtle 1mm/side taper
DOVE_HT = RAIL_DEPTH           # 7mm
RAIL_TOP_Z = BASE_THICK + DOVE_HT  # 10mm — top surface of the rail

# --- Channel (rail profile + clearance) ---
CLEARANCE = 0.2
CHAN_BASE = DOVE_BASE + 2 * CLEARANCE
CHAN_TOP = DOVE_TOP + 2 * CLEARANCE
CHAN_HT = DOVE_HT + 0.3

# --- Frame — tall enough for channel + bump groove + pocket above ---
FRAME_WIDTH = DOVE_BASE + 10.0
FRAME_HT = BASE_THICK + CHAN_HT + SNAP_PROTRUSION + 0.5

SCORE_GAP = 0.5
END_WALL = 2.0

# --- Snap position ---
# Bump centered 3mm from the +X end of the rail. The end wall is
# positioned so the rail tip meets it exactly when the bump aligns
# with the pocket.
SNAP_X = LENGTH / 2 - SNAP_CATCH_LENGTH / 2 - 3.0

# --- Bump / groove ---
BUMP_WIDTH = DOVE_TOP - 1.0                    # slightly narrower than rail top
GROOVE_WIDTH = BUMP_WIDTH + 0.4                # slight clearance around the bump
GROOVE_DEPTH = SNAP_PROTRUSION + 0.1           # slight vertical clearance above bump
GROOVE_TOP_Z = CHAN_HT + GROOVE_DEPTH          # ceiling level of the bump groove


def build() -> Part:
    """Build dovetail slide test with snap detent."""
    piece_offset = max(BASE_WIDTH, FRAME_WIDTH) / 2 + SCORE_GAP / 2

    with BuildPart() as result:
        # ============================================
        # PIECE A — dovetail rail on flat plate
        # ============================================

        # Base plate
        with Locations(Pos(0, -piece_offset, BASE_THICK / 2)):
            Box(LENGTH, BASE_WIDTH, BASE_THICK)

        # Dovetail rail sitting on the base plate
        with Locations(Pos(0, -piece_offset, BASE_THICK)):
            DovetailRail(LENGTH, DOVE_BASE, DOVE_TOP, DOVE_HT)

        # Wall-mount screw holes flanking the rail
        screw_y_offset = (BASE_WIDTH / 2 + DOVE_BASE / 2) / 2
        screw_positions = [
            (0, -piece_offset - screw_y_offset),
            (0, -piece_offset + screw_y_offset),
        ]
        with BuildSketch(Plane.XY.offset(BASE_THICK)):
            with Locations(screw_positions):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-BASE_THICK - 0.1, mode=Mode.SUBTRACT)

        # Snap bump on top of the rail
        with Locations(Pos(SNAP_X, -piece_offset, RAIL_TOP_Z)):
            SnapBump(
                catch_length=SNAP_CATCH_LENGTH,
                ramp_length=SNAP_RAMP_LENGTH,
                width=BUMP_WIDTH,
                protrusion=SNAP_PROTRUSION,
            )

        # ============================================
        # PIECE B — dovetail channel block
        # ============================================

        # Solid frame
        with Locations(Pos(0, piece_offset, FRAME_HT / 2)):
            Box(LENGTH, FRAME_WIDTH, FRAME_HT)

        # Dovetail channel — runs the full length (will be re-closed by end wall)
        with Locations(Pos(0, piece_offset, 0)):
            DovetailChannel(LENGTH + 1, CHAN_BASE, CHAN_TOP, CHAN_HT)

        # End wall at +X: re-fill the open end, then re-cut the dovetail
        # opening through the wall so the rail profile can seat against it.
        end_wall_x = LENGTH / 2 - END_WALL / 2
        with Locations(Pos(end_wall_x, piece_offset, FRAME_HT / 2)):
            Box(END_WALL, FRAME_WIDTH, FRAME_HT)
        with Locations(Pos(end_wall_x, piece_offset, 0)):
            DovetailChannel(END_WALL + 1, CHAN_BASE, CHAN_TOP, CHAN_HT)

        # Bump groove — shallow slot in the channel ceiling along full length
        with Locations(Pos(0, piece_offset, CHAN_HT + GROOVE_DEPTH / 2)):
            Box(LENGTH + 2, GROOVE_WIDTH, GROOVE_DEPTH, mode=Mode.SUBTRACT)

        # Snap pocket — deeper recess with ramps, carved into the groove ceiling
        with Locations(Pos(SNAP_X, piece_offset, GROOVE_TOP_Z)):
            SnapPocket(
                catch_length=SNAP_CATCH_LENGTH,
                ramp_length=SNAP_POCKET_RAMP,
                width=GROOVE_WIDTH,
                extra_depth=SNAP_POCKET_EXTRA,
            )

    return result.part
