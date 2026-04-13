"""Geometry specification for tolerance_test — refactor-safe tests.

These tests validate the *final mesh* only. They do not know or care
whether tolerance_test.py uses builder mode, algebra mode, BasePartObject
subclasses, or raw OCCT. Any refactor that preserves the geometry will
leave every test in this file green with zero edits.

The EXPECTED block at the top is a geometric *specification* — it is
intentionally NOT imported from esp_screen_case.dimensions. Rename or
restructure that module freely; this file is a contract about what the
mesh must look like, independent of how the code computes it.

To refresh golden scalar values after an intentional geometry change:

    make update-goldens
"""

from __future__ import annotations

import pytest

from geometry_helpers import assert_empty, assert_solid

# ============================================================================
# Expected geometry (specification — independent of dimensions.py)
# ============================================================================

# Layout
PIECE_OFFSET_Y = 15.25  # piece A at -Y, piece B at +Y
SCORE_GAP = 0.5
LENGTH = 60.0

# Piece A — dovetail rail on a flat base plate
BASE_PLATE_WIDTH = 30.0
BASE_PLATE_THICK = 3.0
RAIL_BASE_WIDTH = 9.0  # narrow bottom of dovetail
RAIL_TOP_WIDTH = 11.0  # wider top — the undercut
RAIL_HEIGHT = 7.0
RAIL_TOP_Z = BASE_PLATE_THICK + RAIL_HEIGHT  # 10.0

# Piece B — dovetail channel block
#
# Piece B is printed channel-up (flipped 180° about X), so its Z layout
# in the final mesh is inverted relative to "assembly orientation":
#   Z=0 .. ROOF_THICK ................. solid roof sitting on the build plate
#   Z=ROOF_THICK .. FRAME_HEIGHT ....... channel cavity (dovetail, widening down)
FRAME_WIDTH = 19.0
CHANNEL_HEIGHT = 7.1                           # DOVE_HT + 0.1 (tight Z clearance)
ROOF_THICK = 3.0
FRAME_HEIGHT = CHANNEL_HEIGHT + ROOF_THICK     # 10.1
CHANNEL_BASE_WIDTH = 9.4                       # rail base + 2*clearance
CHANNEL_TOP_WIDTH = 11.4                       # rail top + 2*clearance
CHANNEL_WIDE_TOP_Z = FRAME_HEIGHT - CHANNEL_HEIGHT  # 3.0 — channel/roof boundary
CHANNEL_NARROW_BASE_Z = FRAME_HEIGHT                # 10.1 — channel opening (top of print)

# Wall-mount screw holes through piece A's base plate
WALL_SCREW_HOLE_DIAMETER = 4.0
WALL_SCREW_Y_OFFSET = (BASE_PLATE_WIDTH / 2 + RAIL_BASE_WIDTH / 2) / 2  # 9.75
WALL_SCREW_Y_NEG = -PIECE_OFFSET_Y - WALL_SCREW_Y_OFFSET  # -25.0
WALL_SCREW_Y_POS = -PIECE_OFFSET_Y + WALL_SCREW_Y_OFFSET  # -5.5

# Locking screw hole — vertical through-hole that passes through both
# pieces when assembled so one M3 screw can prevent -X sliding
LOCK_X = 24.0
LOCK_HOLE_DIAMETER = 4.0  # same as wall-mount holes

# Golden scalars — captured from STL via `make update-goldens`.
# History: earlier revisions recorded 9554mm³ (piece A) and 10257mm³
# (piece B) when the parts carried an active snap mechanism. The snap
# was dropped in favor of a friction-fit dovetail + M3 lock screw
# after three PETG iterations showed FDM can't hold the tolerances
# a 10mm-scale spring snap needs (snap-fit-reference.md:147).
GOLDEN_TOTAL_VOLUME = 16444.9379
GOLDEN_TOTAL_BBOX = (60.0000, 55.0000, 10.1000)

GOLDEN_A_VOLUME = 9399.0214
GOLDEN_A_BBOX = (60.0000, 30.0000, 10.0000)
GOLDEN_A_CENTROID_Y = -15.2500

GOLDEN_B_VOLUME = 7045.9165
GOLDEN_B_BBOX = (60.0000, 19.0000, 10.1000)
GOLDEN_B_CENTROID_Y = 15.2500

# Tolerances
VOL_TOL = 1.0  # mm³ — STL tessellation noise
DIM_TOL = 0.01  # mm — bounding box / centroid


# ============================================================================
# Group 1 — Golden scalar snapshots (coarse safety net)
# ============================================================================


class TestGoldenScalars:
    """Macro shape — total volume and bounding box, whole mesh and per-body.

    If any of these fail after a refactor, something fundamental changed.
    """

    def test_total_volume(self, tolerance_mesh):
        assert tolerance_mesh.volume == pytest.approx(
            GOLDEN_TOTAL_VOLUME, abs=VOL_TOL
        )

    def test_total_bounding_box(self, tolerance_mesh):
        extents = tuple(tolerance_mesh.bounding_box.extents)
        assert extents == pytest.approx(GOLDEN_TOTAL_BBOX, abs=DIM_TOL)

    def test_piece_a_volume(self, tolerance_bodies):
        piece_a, _ = tolerance_bodies
        assert piece_a.volume == pytest.approx(GOLDEN_A_VOLUME, abs=VOL_TOL)

    def test_piece_a_bounding_box(self, tolerance_bodies):
        piece_a, _ = tolerance_bodies
        extents = tuple(piece_a.bounding_box.extents)
        assert extents == pytest.approx(GOLDEN_A_BBOX, abs=DIM_TOL)

    def test_piece_a_centroid_y(self, tolerance_bodies):
        piece_a, _ = tolerance_bodies
        assert piece_a.centroid[1] == pytest.approx(GOLDEN_A_CENTROID_Y, abs=DIM_TOL)

    def test_piece_b_volume(self, tolerance_bodies):
        _, piece_b = tolerance_bodies
        assert piece_b.volume == pytest.approx(GOLDEN_B_VOLUME, abs=VOL_TOL)

    def test_piece_b_bounding_box(self, tolerance_bodies):
        _, piece_b = tolerance_bodies
        extents = tuple(piece_b.bounding_box.extents)
        assert extents == pytest.approx(GOLDEN_B_BBOX, abs=DIM_TOL)

    def test_piece_b_centroid_y(self, tolerance_bodies):
        _, piece_b = tolerance_bodies
        assert piece_b.centroid[1] == pytest.approx(GOLDEN_B_CENTROID_Y, abs=DIM_TOL)

    def test_two_disconnected_bodies(self, tolerance_mesh):
        """Score gap actually separates the two pieces into distinct solids."""
        from geometry_helpers import split_bodies

        bodies = split_bodies(tolerance_mesh)
        assert len(bodies) == 2


# ============================================================================
# Group 2 — Piece A probes (rail + base plate + lock hole)
# ============================================================================


class TestPieceA:
    """Feature-level probes on the rail piece."""

    def test_base_plate_is_solid(self, tolerance_bodies):
        """Interior of the base plate (avoiding screw holes) is material."""
        piece_a, _ = tolerance_bodies
        z_mid = BASE_PLATE_THICK / 2  # 1.5, mid-thickness
        probes = [
            (0.0, -PIECE_OFFSET_Y, z_mid),        # plate center
            (-25.0, -10.0, z_mid),                # -X area, clear of holes
            (25.0, -20.0, z_mid),                 # +X area, clear of holes
            (15.0, -2.0, z_mid),                  # near +Y edge of plate
        ]
        assert_solid(piece_a, probes, "base plate interior")

    def test_rail_interior_is_solid(self, tolerance_bodies):
        """Rail body has material along its length at mid-height."""
        piece_a, _ = tolerance_bodies
        z_mid = BASE_PLATE_THICK + RAIL_HEIGHT / 2  # 6.5
        probes = [
            (-20.0, -PIECE_OFFSET_Y, z_mid),
            (0.0, -PIECE_OFFSET_Y, z_mid),
            (20.0, -PIECE_OFFSET_Y, z_mid),  # clear of the lock hole at X=24
        ]
        assert_solid(piece_a, probes, "rail interior")

    def test_rail_dovetail_is_undercut_at_base(self, tolerance_bodies):
        """Just outside RAIL_BASE_WIDTH near the bottom of the rail is empty.

        This is the distinguishing feature of a dovetail — the base is
        narrower than the top. A regression that forgot the taper cut
        (leaving a full-width rail) would fail this test.
        """
        piece_a, _ = tolerance_bodies
        z_near_bottom = BASE_PLATE_THICK + 0.3  # 3.3 — just into the rail
        # At z=3.3, rail width is barely above RAIL_BASE_WIDTH (≈9.09 from
        # linear interpolation). Half-width ~4.54. A point at dy=±4.8 is
        # clearly outside the rail trapezoid at that height.
        dy = 4.8
        probes = [
            (-20.0, -PIECE_OFFSET_Y + dy, z_near_bottom),
            (-20.0, -PIECE_OFFSET_Y - dy, z_near_bottom),
            (0.0, -PIECE_OFFSET_Y + dy, z_near_bottom),
            (0.0, -PIECE_OFFSET_Y - dy, z_near_bottom),
        ]
        assert_empty(piece_a, probes, "dovetail undercut at base")

    def test_rail_top_is_wide(self, tolerance_bodies):
        """Near RAIL_TOP_WIDTH/2 at the top of the rail is inside the body.

        This catches the opposite failure mode — a refactor that made the
        rail narrower at the top (i.e. not a dovetail). Combined with the
        previous test, these two pin the trapezoid shape.
        """
        piece_a, _ = tolerance_bodies
        z_near_top = RAIL_TOP_Z - 0.3  # 9.7 — just inside the rail top
        dy = 5.0  # RAIL_TOP_WIDTH/2 = 5.5; dy=5.0 is clearly inside
        probes = [
            (-20.0, -PIECE_OFFSET_Y + dy, z_near_top),
            (-20.0, -PIECE_OFFSET_Y - dy, z_near_top),
            (0.0, -PIECE_OFFSET_Y + dy, z_near_top),
            (0.0, -PIECE_OFFSET_Y - dy, z_near_top),
        ]
        assert_solid(piece_a, probes, "rail top width")

    def test_above_rail_is_empty(self, tolerance_bodies):
        """Above the rail top is empty — no snap bump, no cantilever, no
        other features protruding above RAIL_TOP_Z on piece A."""
        piece_a, _ = tolerance_bodies
        z_above = RAIL_TOP_Z + 0.5  # 10.5 — clearly above rail top
        probes = [
            (-25.0, -PIECE_OFFSET_Y, z_above),
            (-10.0, -PIECE_OFFSET_Y, z_above),
            (0.0, -PIECE_OFFSET_Y, z_above),
            (15.0, -PIECE_OFFSET_Y, z_above),
            (24.0, -PIECE_OFFSET_Y, z_above),  # at LOCK_X too
        ]
        assert_empty(piece_a, probes, "above rail top")

    def test_wall_mount_screw_holes_are_open(self, tolerance_bodies):
        """Both wall-mount screw holes are cut through the base plate."""
        piece_a, _ = tolerance_bodies
        z_mid = BASE_PLATE_THICK / 2  # 1.5, mid-plate
        probes = [
            (0.0, WALL_SCREW_Y_NEG, z_mid),  # -Y hole
            (0.0, WALL_SCREW_Y_POS, z_mid),  # +Y hole
        ]
        assert_empty(piece_a, probes, "wall-mount screw holes")

    def test_lock_hole_passes_through_rail_and_plate(self, tolerance_bodies):
        """Locking screw hole is cut through the full Z extent of piece A
        at LOCK_X — rail top, rail mid, and base plate levels are all
        empty at (LOCK_X, rail-center)."""
        piece_a, _ = tolerance_bodies
        probes = [
            (LOCK_X, -PIECE_OFFSET_Y, RAIL_TOP_Z - 0.1),       # near rail top
            (LOCK_X, -PIECE_OFFSET_Y, BASE_PLATE_THICK + RAIL_HEIGHT / 2),  # rail middle
            (LOCK_X, -PIECE_OFFSET_Y, BASE_PLATE_THICK + 0.1),  # just inside rail base
            (LOCK_X, -PIECE_OFFSET_Y, BASE_PLATE_THICK / 2),    # base plate middle
        ]
        assert_empty(piece_a, probes, "lock hole through piece A")

    def test_lock_hole_is_local_in_x(self, tolerance_bodies):
        """Lock hole doesn't span the whole rail — probes at X values
        several mm away from LOCK_X at the same Y, Z should be solid."""
        piece_a, _ = tolerance_bodies
        z_mid_rail = BASE_PLATE_THICK + RAIL_HEIGHT / 2  # 6.5
        probes = [
            (LOCK_X - 3.0, -PIECE_OFFSET_Y, z_mid_rail),
            (LOCK_X + 3.0, -PIECE_OFFSET_Y, z_mid_rail),
            (0.0, -PIECE_OFFSET_Y, z_mid_rail),
        ]
        assert_solid(piece_a, probes, "rail solid away from lock hole X")


# ============================================================================
# Group 3 — Piece B probes (channel + end wall + lock hole)
# ============================================================================


class TestPieceB:
    """Feature-level probes on the channel piece."""

    def test_frame_is_solid_outside_channel(self, tolerance_bodies):
        """The frame walls, outside the channel cavity, contain material."""
        _, piece_b = tolerance_bodies
        # Frame Y range is [5.75, 24.75]. Piece B prints channel-up so
        # the solid roof sits at Z∈[0, 3] and the channel cavity fills
        # Z∈[3, 10.1] — probes need to avoid (center Y, high Z).
        probes = [
            (0.0, 6.5, 5.0),                          # -Y wall, mid height
            (0.0, 24.0, 5.0),                         # +Y wall, mid height
            (-20.0, PIECE_OFFSET_Y, 1.5),             # roof interior, center Y
            (10.0, PIECE_OFFSET_Y, 1.5),              # roof interior, another X
            (0.0, 6.5, 8.0),                          # -Y wall at channel height
        ]
        assert_solid(piece_b, probes, "frame interior")

    def test_channel_interior_is_empty(self, tolerance_bodies):
        """Channel cavity is cut along the full length at mid-channel Z."""
        _, piece_b = tolerance_bodies
        z_channel = (CHANNEL_WIDE_TOP_Z + CHANNEL_NARROW_BASE_Z) / 2  # ~6.55
        probes = [
            (-25.0, PIECE_OFFSET_Y, z_channel),
            (-10.0, PIECE_OFFSET_Y, z_channel),
            (0.0, PIECE_OFFSET_Y, z_channel),
            (10.0, PIECE_OFFSET_Y, z_channel),
            (20.0, PIECE_OFFSET_Y, z_channel),        # clear of end wall at X=28
        ]
        assert_empty(piece_b, probes, "channel interior")

    def test_channel_wide_top_is_wider_than_narrow_base(self, tolerance_bodies):
        """Taper check — channel half-width ≈5.7 at wide top vs ≈4.7 at narrow base.

        Probes at dy=5.0 from centerline: empty just inside the wide top
        (inside the widened region), solid just inside the narrow base
        end (outside the narrow region, inside the surrounding frame).
        This pins the channel taper.
        """
        _, piece_b = tolerance_bodies
        dy = 5.0  # between CHANNEL_BASE_WIDTH/2=4.7 and CHANNEL_TOP_WIDTH/2=5.7
        x = 0.0  # middle of channel, far from end wall and lock hole

        # Just inside the wide top — inside the widened channel region
        empty_probes = [
            (x, PIECE_OFFSET_Y + dy, CHANNEL_WIDE_TOP_Z + 0.2),
            (x, PIECE_OFFSET_Y - dy, CHANNEL_WIDE_TOP_Z + 0.2),
        ]
        assert_empty(piece_b, empty_probes, "channel widened top")

        # Just inside the narrow base end — outside the narrow region, inside frame
        solid_probes = [
            (x, PIECE_OFFSET_Y + dy, CHANNEL_NARROW_BASE_Z - 0.5),
            (x, PIECE_OFFSET_Y - dy, CHANNEL_NARROW_BASE_Z - 0.5),
        ]
        assert_solid(piece_b, solid_probes, "channel narrow base surrounds")

    def test_end_wall_has_dovetail_hole(self, tolerance_bodies):
        """End wall at +X has a channel-shaped opening cut through it."""
        _, piece_b = tolerance_bodies
        x_end_wall = 29.0  # inside END_WALL region X=[28, 30]

        # Inside the dovetail hole — empty (probe at mid-channel height)
        z_channel = (CHANNEL_WIDE_TOP_Z + CHANNEL_NARROW_BASE_Z) / 2  # ~6.55
        assert_empty(
            piece_b,
            [(x_end_wall, PIECE_OFFSET_Y, z_channel)],
            "end wall dovetail opening",
        )

        # Outside the hole (in Y, inside frame) — solid
        assert_solid(
            piece_b,
            [(x_end_wall, 6.5, 1.5)],  # -Y side of frame, in the roof region
            "end wall solid material",
        )

    def test_lock_hole_passes_through_roof(self, tolerance_bodies):
        """Locking screw hole is cut through piece B's roof at LOCK_X, so
        an M3 screw can drop through into piece A's matching hole below."""
        _, piece_b = tolerance_bodies
        assert_empty(
            piece_b,
            [(LOCK_X, PIECE_OFFSET_Y, ROOF_THICK / 2)],  # mid-roof
            "lock hole through roof",
        )
        # Away from LOCK_X at the same Z should be solid roof
        assert_solid(
            piece_b,
            [
                (0.0, PIECE_OFFSET_Y, ROOF_THICK / 2),
                (LOCK_X - 3.0, PIECE_OFFSET_Y, ROOF_THICK / 2),
            ],
            "roof solid away from lock hole X",
        )


# ============================================================================
# Group 4 — Fit check (the whole point of the part)
# ============================================================================


class TestRailFitsInChannel:
    """Rail profile corners transposed into piece B are inside the channel cavity.

    This is the assembly sanity check. If the channel is ever too small
    (or the rail ever too big) to accept the profile with clearance, this
    test fails regardless of what layer of the code changed.

    We transpose by translating rail-local (dy, dz) offsets onto the
    channel centerline, so the test only cares about relative profile
    dimensions — not absolute world positions.
    """

    # Rail half-widths at specific Z offsets from the base (z=0 at rail bottom)
    RAIL_BASE_HALF = RAIL_BASE_WIDTH / 2  # 4.5
    RAIL_TOP_HALF = RAIL_TOP_WIDTH / 2    # 5.5

    def test_rail_bottom_corners_fit_in_channel_narrow_end(self, tolerance_bodies):
        """Rail's narrow base corners are inside the channel's narrow end."""
        _, piece_b = tolerance_bodies
        z = CHANNEL_NARROW_BASE_Z - 0.1  # just inside the narrow opening
        probes = []
        for x in [-20.0, 0.0, 20.0]:  # away from end wall and lock hole
            probes.append((x, PIECE_OFFSET_Y + self.RAIL_BASE_HALF, z))
            probes.append((x, PIECE_OFFSET_Y - self.RAIL_BASE_HALF, z))
        assert_empty(piece_b, probes, "rail base corners fit in channel narrow end")

    def test_rail_top_corners_fit_in_channel_wide_end(self, tolerance_bodies):
        """Rail's wider top corners are inside the channel's widened end."""
        _, piece_b = tolerance_bodies
        z = CHANNEL_WIDE_TOP_Z + 0.3  # just inside the widened end
        probes = []
        for x in [-20.0, 0.0, 20.0]:
            probes.append((x, PIECE_OFFSET_Y + self.RAIL_TOP_HALF, z))
            probes.append((x, PIECE_OFFSET_Y - self.RAIL_TOP_HALF, z))
        assert_empty(piece_b, probes, "rail top corners fit in channel wide end")
