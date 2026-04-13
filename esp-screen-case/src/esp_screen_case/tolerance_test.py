"""Tolerance test piece — dovetail rail and channel that slide together.

Two pieces printed side by side, snap apart at the score line:
- Piece A: flat plate with a dovetail rail (narrow base, wider top)
- Piece B: block with a matching dovetail channel, open at -X end

Cross-section (looking at the open entry end):

Piece A (rail):              Piece B (channel):
    ╲━━━━╱  wider top         ┌──╱      ╲──┐
     ╲  ╱                     │ ╱        ╲ │
      ╲╱    narrow base       │╱ dovetail ╲│
──────────────                └────────────┘
│   base plate  │

Assembly:
    Slide B onto A from -X toward +X until the rail tip meets B's
    end wall. The dovetail's undercut locks B vertically (gravity
    can't pull it off). The end wall stops +X motion. Friction from
    the tight-clearance dovetail resists -X motion.

    For positive locking, a single M3 screw drops through the
    prepunched hole near the +X end: top → through piece B's roof →
    through piece A's rail → through the base plate → nut on the
    back. One screw, no flex features.

History:
    Earlier versions had an internal snap mechanism (bump-in-groove
    with a ramped pocket, later a cantilever tongue carved into the
    rail). Three iterations in PETG confirmed that active snaps at
    this 10mm scale don't click cleanly in FDM — matching
    `notes/projects/ESP Screen Case/snap-fit-reference.md:147`
    ("clips are useless — switched to M3 bolts"). The SnapBump /
    SnapPocket primitives still live in `cadlib.py` for future use.
"""

from build123d import (
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Pos,
    add,
    extrude,
)

from esp_screen_case.cadlib import DovetailChannel, DovetailRail
from esp_screen_case.dimensions import (
    RAIL_DEPTH,
    RAIL_WIDTH,
    SCREW_HOLE_DIAMETER,
)

# --- Test piece sizing ---
LENGTH = 60.0
BASE_WIDTH = 30.0
BASE_THICK = 3.0

# --- Dovetail rail ---
DOVE_BASE = RAIL_WIDTH - 1.0   # 9mm base (narrow)
DOVE_TOP = RAIL_WIDTH + 1.0    # 11mm top (wide) — subtle 1mm/side taper
DOVE_HT = RAIL_DEPTH           # 7mm
RAIL_TOP_Z = BASE_THICK + DOVE_HT  # 10mm — top surface of the rail

# --- Channel (rail profile + clearance) ---
CLEARANCE = 0.2                # 0.1mm each Y side — PETG slide fit
CHAN_BASE = DOVE_BASE + 2 * CLEARANCE
CHAN_TOP = DOVE_TOP + 2 * CLEARANCE
CHAN_HT = DOVE_HT + 0.1        # 0.1mm Z slop

# --- Frame dimensions ---
FRAME_WIDTH = DOVE_BASE + 10.0
ROOF_THICK = 3.0               # solid material above the channel cavity
FRAME_HT = CHAN_HT + ROOF_THICK  # 10.1mm total

SCORE_GAP = 0.5
END_WALL = 2.0

# --- Locking screw hole ---
# A single vertical hole near the +X end drops through both pieces so
# an M3 screw can lock B against -X motion. Positioned clear of the
# end wall and the wall-mount screw holes.
LOCK_X = 24.0


def _build_piece_b() -> Part:
    """Construct piece B at the origin in assembly orientation.

    Built as a standalone `BuildPart` *outside* the main builder so
    its internal ADD/SUBTRACT ops don't leak into the parent context.
    The caller rotates and translates the returned part before adding
    it to the final assembly.
    """
    with BuildPart() as piece_b:
        # Solid frame
        with Locations(Pos(0, 0, FRAME_HT / 2)):
            Box(LENGTH, FRAME_WIDTH, FRAME_HT)

        # Dovetail channel — runs the full length (will be re-closed by end wall)
        with Locations(Pos(0, 0, 0)):
            DovetailChannel(LENGTH + 1, CHAN_BASE, CHAN_TOP, CHAN_HT)

        # End wall at +X: re-fill the open end, then re-cut the dovetail
        # opening through the wall so the rail profile can seat against it.
        end_wall_x = LENGTH / 2 - END_WALL / 2
        with Locations(Pos(end_wall_x, 0, FRAME_HT / 2)):
            Box(END_WALL, FRAME_WIDTH, FRAME_HT)
        with Locations(Pos(end_wall_x, 0, 0)):
            DovetailChannel(END_WALL + 1, CHAN_BASE, CHAN_TOP, CHAN_HT)

        # Locking screw hole through the roof, above the channel cavity.
        # Extends from the top of piece B down to the channel ceiling;
        # the cavity below is already open so the screw continues
        # through into the rail below in assembly.
        with BuildSketch(Plane.XY.offset(FRAME_HT)):
            with Locations((LOCK_X, 0)):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-(ROOF_THICK + 0.1), mode=Mode.SUBTRACT)

    return piece_b.part


def build() -> Part:
    """Build dovetail slide test (no active snap; locks via M3 screw)."""
    piece_offset = max(BASE_WIDTH, FRAME_WIDTH) / 2 + SCORE_GAP / 2

    # Piece B is built first, outside the main builder, so it can be
    # flipped (channel-up for print quality) without leaking primitives
    # into the outer context — nested BuildPart doesn't isolate.
    flipped_piece_b = _build_piece_b().rotate(Axis.X, 180).moved(
        Location((0, piece_offset, FRAME_HT))
    )

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

        # Wall-mount screw holes flanking the rail (through the base plate)
        wall_screw_y_offset = (BASE_WIDTH / 2 + DOVE_BASE / 2) / 2
        wall_screw_positions = [
            (0, -piece_offset - wall_screw_y_offset),
            (0, -piece_offset + wall_screw_y_offset),
        ]
        with BuildSketch(Plane.XY.offset(BASE_THICK)):
            with Locations(wall_screw_positions):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-BASE_THICK - 0.1, mode=Mode.SUBTRACT)

        # Locking screw hole through the rail + base plate at LOCK_X.
        # Aligns with piece B's matching hole through the roof when
        # assembled, so one screw spans both parts.
        with BuildSketch(Plane.XY.offset(RAIL_TOP_Z)):
            with Locations((LOCK_X, -piece_offset)):
                Circle(SCREW_HOLE_DIAMETER / 2)
        extrude(amount=-(RAIL_TOP_Z + 0.1), mode=Mode.SUBTRACT)

        # ============================================
        # PIECE B — dovetail channel block (flipped for print quality)
        #
        # Piece B prints channel-up: the solid "roof" lands on the
        # build plate and the dovetail walls print as near-vertical
        # perimeters instead of an ~11mm-wide bridge. Geometry was
        # built at origin and flipped above.
        # ============================================
        add(flipped_piece_b)

    return result.part
