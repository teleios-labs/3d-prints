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
    SNAP_CANT_LENGTH,
    SNAP_CANT_SLOT_HEIGHT,
    SNAP_CANT_THICK,
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
# Z clearance is tight (0.1mm) so the rail's vertical position inside
# the channel is predictable — the cantilever snap relies on the bump
# sitting at a known height relative to the groove ceiling.
CLEARANCE = 0.2
CHAN_BASE = DOVE_BASE + 2 * CLEARANCE
CHAN_TOP = DOVE_TOP + 2 * CLEARANCE
CHAN_HT = DOVE_HT + 0.1

# --- Frame — tall enough for channel + bump groove + pocket + solid roof ---
# ROOF_THICK is the solid material above the deepest point of the snap
# pocket. The pocket is a short cavity (~5.5mm long including ramps) in
# the channel ceiling, so its top layers print as a bridge — we want it
# thick enough to feel rigid when the bump clicks in, not flex like a
# drumhead. 5mm = 25 layers at 0.2mm, comfortably solid for PETG.
FRAME_WIDTH = DOVE_BASE + 10.0
ROOF_THICK = 5.0

SCORE_GAP = 0.5
END_WALL = 2.0

# --- Snap position ---
# Bump centered 3mm from the +X end of the rail. The end wall is
# positioned so the rail tip meets it exactly when the bump aligns
# with the pocket.
SNAP_X = LENGTH / 2 - SNAP_CATCH_LENGTH / 2 - 3.0

# --- Bump / groove ---
BUMP_WIDTH = DOVE_TOP - 1.0                    # slightly narrower than rail top
# Groove is exactly as wide as the channel ceiling so the cavity walls
# stay flush — no inward lip at the channel/groove transition. (The
# bump still gets its Y clearance via BUMP_WIDTH being narrower.)
GROOVE_WIDTH = CHAN_TOP
# Groove depth is set so `SNAP_PROTRUSION - GROOVE_DEPTH - Z_slop ≈ 0.2mm`
# of interference above the groove ceiling. The rail's cantilever tongue
# flexes to absorb it during sliding and snaps back at the pocket.
GROOVE_DEPTH = 1.0
GROOVE_TOP_Z = CHAN_HT + GROOVE_DEPTH          # ceiling level of the bump groove
FRAME_HT = GROOVE_TOP_Z + SNAP_POCKET_EXTRA + ROOF_THICK


def _build_piece_b() -> Part:
    """Construct piece B at the origin in assembly orientation.

    Built as a standalone `BuildPart` *outside* the main builder so its
    internal ADD/SUBTRACT ops don't leak into the parent context. The
    caller is responsible for any rotation and translation before adding
    the result to the final assembly.
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

        # Bump groove — shallow slot in the channel ceiling along full length
        with Locations(Pos(0, 0, CHAN_HT + GROOVE_DEPTH / 2)):
            Box(LENGTH + 2, GROOVE_WIDTH, GROOVE_DEPTH, mode=Mode.SUBTRACT)

        # Snap pocket — deeper recess with ramps, carved into the groove ceiling
        with Locations(Pos(SNAP_X, 0, GROOVE_TOP_Z)):
            SnapPocket(
                catch_length=SNAP_CATCH_LENGTH,
                ramp_length=SNAP_POCKET_RAMP,
                width=GROOVE_WIDTH,
                extra_depth=SNAP_POCKET_EXTRA,
            )
    return piece_b.part


def build() -> Part:
    """Build dovetail slide test with snap detent."""
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

        # Cantilever slot — cut a horizontal void inside the rail so the
        # top `SNAP_CANT_THICK` of material above the slot acts as a
        # flexing tongue anchored at the -X end of the slot and free at
        # the +X (rail tip) end. The snap bump at SNAP_X sits near the
        # tongue's free end and deflects downward when it meets the
        # channel's groove ceiling, then springs back at the pocket.
        slot_x_end = LENGTH / 2 + 0.5              # 0.5mm past rail +X end
        slot_x_start = slot_x_end - SNAP_CANT_LENGTH
        slot_z_top = RAIL_TOP_Z - SNAP_CANT_THICK   # slot ceiling = tongue bottom
        slot_z_bot = slot_z_top - SNAP_CANT_SLOT_HEIGHT
        with Locations(
            Pos(
                (slot_x_start + slot_x_end) / 2,
                -piece_offset,
                (slot_z_top + slot_z_bot) / 2,
            )
        ):
            Box(
                slot_x_end - slot_x_start,
                RAIL_WIDTH + 2,  # wider than the rail for a clean cut-through in Y
                slot_z_top - slot_z_bot,
                mode=Mode.SUBTRACT,
            )

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
        # PIECE B — dovetail channel block (flipped for print quality)
        #
        # Piece B prints channel-up: the solid "roof" lands on the build
        # plate and the channel's wide top — the surface the rail's
        # undercut actually contacts — prints as near-vertical walls
        # instead of an ~11mm-wide bridge. Same win at the groove and
        # snap pocket. Geometry was built at origin and flipped above.
        # ============================================
        add(flipped_piece_b)

    return result.part
