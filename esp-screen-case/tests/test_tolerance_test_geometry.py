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

    uv run python esp-screen-case/tests/capture_tolerance_golden.py

...then paste the printed block into the GOLDEN_* constants below.
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

# Piece B — dovetail channel
FRAME_WIDTH = 19.0
FRAME_HEIGHT = 13.8
CHANNEL_BASE_WIDTH = 9.4  # narrow at floor (rail base + 2*clearance)
CHANNEL_TOP_WIDTH = 11.4  # wider at ceiling
CHANNEL_HEIGHT = 7.3
CHANNEL_CEILING_Z = CHANNEL_HEIGHT  # 7.3

# Snap mechanism
SNAP_X = 26.25  # center X of the snap catch on the rail / pocket on the channel
SNAP_PROTRUSION = 1.0
SNAP_CATCH_LENGTH = 1.5
SNAP_POCKET_EXTRA_DEPTH = 0.4
BUMP_GROOVE_Z_MIN = CHANNEL_CEILING_Z  # 7.3
BUMP_GROOVE_Z_MAX = CHANNEL_CEILING_Z + SNAP_PROTRUSION + 0.1  # 8.4
POCKET_Z_MAX = BUMP_GROOVE_Z_MAX + SNAP_POCKET_EXTRA_DEPTH + 0.05  # ~8.85

# Screw holes through base plate — two, flanking the rail
SCREW_HOLE_DIAMETER = 4.0
SCREW_Y_OFFSET = (BASE_PLATE_WIDTH / 2 + RAIL_BASE_WIDTH / 2) / 2  # 9.75
SCREW_Y_NEG = -PIECE_OFFSET_Y - SCREW_Y_OFFSET  # -25.0
SCREW_Y_POS = -PIECE_OFFSET_Y + SCREW_Y_OFFSET  # -5.5

# Golden scalars — captured 2026-04-09 from cadlib-based construction.
#
# History: initial capture from the original inline builder code was
# ~26mm³ (piece A) and ~51mm³ (piece B) different from these values.
# The old construction used "wide box + subtract corner triangles" for
# the dovetail, which left tiny slivers of extra material near the
# corners due to 0.1mm clipping overshoots. The refactored Dovetail
# class extrudes a clean trapezoidal sketch directly, matching the
# theoretical dovetail volume (9554.60 mm³ for piece A) to within
# tessellation noise.
#
# To recapture: uv run python esp-screen-case/tests/capture_tolerance_golden.py
GOLDEN_TOTAL_VOLUME = 20019.1986
GOLDEN_TOTAL_BBOX = (60.0000, 55.0000, 13.8000)

GOLDEN_A_VOLUME = 9554.6330
GOLDEN_A_BBOX = (60.0000, 30.0000, 11.0000)
GOLDEN_A_CENTROID_Y = -15.2500

GOLDEN_B_VOLUME = 10464.5656
GOLDEN_B_BBOX = (60.0000, 19.0000, 13.8000)
GOLDEN_B_CENTROID_Y = 15.2500

# Tolerances
VOL_TOL = 1.0  # mm³ — STL tessellation noise
DIM_TOL = 0.01  # mm — bounding box / centroid

# Away-from-snap X values for probe points that should be unaffected by the
# snap bump / pocket features (safe margin beyond the snap + ramp region)
X_AWAY_FROM_SNAP = [-25.0, -10.0, 0.0, 10.0, 20.0]


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
# Group 2 — Piece A probes (rail + base plate + snap bump)
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
            (20.0, -PIECE_OFFSET_Y, z_mid),  # clear of snap at X=26.25
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

    def test_above_rail_is_empty_away_from_snap(self, tolerance_bodies):
        """Above the rail top, outside the snap bump region, is empty."""
        piece_a, _ = tolerance_bodies
        z_above = RAIL_TOP_Z + 0.5  # 10.5 — above rail top, at bump Z level
        probes = [
            (-25.0, -PIECE_OFFSET_Y, z_above),
            (-10.0, -PIECE_OFFSET_Y, z_above),
            (0.0, -PIECE_OFFSET_Y, z_above),
            (15.0, -PIECE_OFFSET_Y, z_above),
        ]
        assert_empty(piece_a, probes, "above rail away from snap")

    def test_snap_bump_exists_at_snap_x(self, tolerance_bodies):
        """Catch body is present at SNAP_X on top of the rail."""
        piece_a, _ = tolerance_bodies
        z_catch = RAIL_TOP_Z + SNAP_PROTRUSION / 2  # 10.5, middle of catch
        probes = [
            (SNAP_X, -PIECE_OFFSET_Y, z_catch),
            (SNAP_X - 0.3, -PIECE_OFFSET_Y, z_catch),  # still inside catch
            (SNAP_X + 0.3, -PIECE_OFFSET_Y, z_catch),
        ]
        assert_solid(piece_a, probes, "snap catch at SNAP_X")

    def test_screw_holes_are_open(self, tolerance_bodies):
        """Both screw holes are actually empty through the plate."""
        piece_a, _ = tolerance_bodies
        z_mid = BASE_PLATE_THICK / 2  # 1.5, mid-plate
        probes = [
            (0.0, SCREW_Y_NEG, z_mid),  # -Y hole
            (0.0, SCREW_Y_POS, z_mid),  # +Y hole
        ]
        assert_empty(piece_a, probes, "screw holes")


# ============================================================================
# Group 3 — Piece B probes (channel + groove + pocket + end wall)
# ============================================================================


class TestPieceB:
    """Feature-level probes on the channel piece."""

    def test_frame_is_solid_outside_channel(self, tolerance_bodies):
        """The frame walls, outside all cuts, contain material."""
        _, piece_b = tolerance_bodies
        # Points well outside channel in Y, well above channel ceiling,
        # far from snap pocket, inside frame Y=[5.75, 24.75]
        probes = [
            (0.0, 6.5, 5.0),                          # -Y wall, mid height
            (0.0, 24.0, 5.0),                         # +Y wall, mid height
            (-20.0, PIECE_OFFSET_Y, 10.5),            # above groove, away from snap
            (10.0, PIECE_OFFSET_Y, 10.5),             # above groove, away from snap
            (0.0, 6.5, 10.0),                         # upper corner
        ]
        assert_solid(piece_b, probes, "frame interior")

    def test_channel_floor_is_empty(self, tolerance_bodies):
        """Channel cavity is cut along the full length at the floor level."""
        _, piece_b = tolerance_bodies
        z_floor = 1.0  # well inside channel Z=[0, 7.3]
        probes = [
            (-25.0, PIECE_OFFSET_Y, z_floor),
            (-10.0, PIECE_OFFSET_Y, z_floor),
            (0.0, PIECE_OFFSET_Y, z_floor),
            (10.0, PIECE_OFFSET_Y, z_floor),
            (20.0, PIECE_OFFSET_Y, z_floor),          # clear of end wall at X=28
        ]
        assert_empty(piece_b, probes, "channel floor")

    def test_channel_ceiling_is_wider_than_floor(self, tolerance_bodies):
        """Taper check — channel half-width ≈5.5 at ceiling but only ≈4.7 at floor.

        Probes at dy=5.0 from centerline: empty near the ceiling (inside
        the widened top), solid near the floor (outside the narrow base,
        inside the surrounding frame). This pins the channel taper.
        """
        _, piece_b = tolerance_bodies
        dy = 5.0  # between CHANNEL_BASE_WIDTH/2=4.7 and CHANNEL_TOP_WIDTH/2=5.7
        x = 0.0  # middle of channel, far from snap & end wall

        # Near the ceiling — inside the widened channel
        empty_probes = [
            (x, PIECE_OFFSET_Y + dy, CHANNEL_CEILING_Z - 0.2),
            (x, PIECE_OFFSET_Y - dy, CHANNEL_CEILING_Z - 0.2),
        ]
        assert_empty(piece_b, empty_probes, "channel widened top")

        # Near the floor — outside the narrow channel base, still inside frame
        solid_probes = [
            (x, PIECE_OFFSET_Y + dy, 0.5),
            (x, PIECE_OFFSET_Y - dy, 0.5),
        ]
        assert_solid(piece_b, solid_probes, "channel narrow base surrounds")

    def test_bump_groove_runs_full_length(self, tolerance_bodies):
        """Groove is empty at every probe X along the length."""
        _, piece_b = tolerance_bodies
        z_groove = (BUMP_GROOVE_Z_MIN + BUMP_GROOVE_Z_MAX) / 2  # 7.85
        probes = [(x, PIECE_OFFSET_Y, z_groove) for x in [-25.0, -10.0, 0.0, 10.0, 20.0]]
        assert_empty(piece_b, probes, "bump groove full length")

    def test_snap_pocket_deeper_than_groove(self, tolerance_bodies):
        """Above the groove, there is pocket material only at SNAP_X.

        This is the snap click feature — a deeper recess at a single X.
        Everywhere else at the same Z level should be solid frame.
        """
        _, piece_b = tolerance_bodies
        z_pocket = BUMP_GROOVE_Z_MAX + SNAP_POCKET_EXTRA_DEPTH / 2  # 8.6

        # Inside pocket at SNAP_X
        assert_empty(
            piece_b,
            [(SNAP_X, PIECE_OFFSET_Y, z_pocket)],
            "snap pocket recess",
        )

        # Solid frame at the same Z level, well away from SNAP_X
        assert_solid(
            piece_b,
            [
                (-10.0, PIECE_OFFSET_Y, z_pocket),
                (0.0, PIECE_OFFSET_Y, z_pocket),
                (10.0, PIECE_OFFSET_Y, z_pocket),
            ],
            "frame above groove away from SNAP_X",
        )

    def test_end_wall_has_dovetail_hole(self, tolerance_bodies):
        """End wall at +X has a channel-shaped opening cut through it."""
        _, piece_b = tolerance_bodies
        x_end_wall = 29.0  # inside END_WALL region X=[28, 30]

        # Inside the dovetail hole — empty
        assert_empty(
            piece_b,
            [(x_end_wall, PIECE_OFFSET_Y, 1.0)],  # channel floor level
            "end wall dovetail opening",
        )

        # Outside the hole (in Y, inside frame) — solid
        assert_solid(
            piece_b,
            [(x_end_wall, 6.5, 5.0)],  # -Y side of frame, mid height
            "end wall solid material",
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

    # Channel centerline coordinates in piece B:
    #   Y = +PIECE_OFFSET_Y, Z = 0 at the channel floor, up to CHANNEL_HEIGHT
    # Rail profile points (relative to rail base): (dy, dz)
    #   Bottom outer corners: (±RAIL_BASE_HALF, 0)  → near channel floor
    #   Top outer corners:    (±RAIL_TOP_HALF, RAIL_HEIGHT) → near ceiling

    def test_rail_bottom_corners_fit_in_channel_floor(self, tolerance_bodies):
        """Rail's narrow base corners are inside the channel base width."""
        _, piece_b = tolerance_bodies
        z = 0.1  # just above channel floor
        probes = []
        for x in [-20.0, 0.0, 20.0]:  # away from snap and end wall
            probes.append((x, PIECE_OFFSET_Y + self.RAIL_BASE_HALF, z))
            probes.append((x, PIECE_OFFSET_Y - self.RAIL_BASE_HALF, z))
        assert_empty(piece_b, probes, "rail base corners fit in channel base")

    def test_rail_top_corners_fit_in_channel_ceiling(self, tolerance_bodies):
        """Rail's wider top corners are inside the channel widened top."""
        _, piece_b = tolerance_bodies
        z = CHANNEL_HEIGHT - 0.3  # just below channel ceiling
        probes = []
        for x in [-20.0, 0.0, 20.0]:
            probes.append((x, PIECE_OFFSET_Y + self.RAIL_TOP_HALF, z))
            probes.append((x, PIECE_OFFSET_Y - self.RAIL_TOP_HALF, z))
        assert_empty(piece_b, probes, "rail top corners fit in channel top")
