"""Geometry specification for wall_bracket — refactor-safe tests.

Tests validate the final mesh only. The EXPECTED block below is a
spec contract — intentionally NOT imported from dimensions.py. Rename
constants there freely; this file captures what the mesh must look
like regardless.

Refresh golden scalars after an intentional geometry change:

    make update-goldens
"""

from __future__ import annotations

import pytest
import trimesh
from build123d import export_stl

from esp_screen_case.wall_bracket import build
from geometry_helpers import assert_empty, assert_solid

# ============================================================================
# Expected geometry (spec — independent of dimensions.py)
# ============================================================================

# Upper hub and shelf flange (X = width, Y = height, Z = thickness from wall)
UPPER_HUB_X = 30.0
SHELF_X = 40.0               # shelf flange is wider than upper hub
HUB_Y = 73.0                 # total hub height = shelf 15 + rail 50 + lead-in 8
HUB_Z = 4.0

# Dovetail rail on the upper hub's front face
RAIL_BASE_WIDTH = 10.0       # narrow bottom — at hub front face (Z = HUB_Z)
RAIL_TOP_WIDTH = 11.0        # wider top (undercut) — at Z = HUB_Z + RAIL_DEPTH
RAIL_DEPTH = 7.0             # proud of the hub front face
RAIL_LENGTH = 50.0           # along Y (vertical in wall coordinates)

# Y layout built from the hub bottom up
LEAD_IN_STRIP = 8.0          # 8mm strip at the top of the hub, above the rail
SHELF_Y = 15.0               # bottom 15mm of the hub is the wider shelf flange
HUB_BOTTOM_Y = -HUB_Y / 2                          # -36.5
SHELF_TOP_Y = HUB_BOTTOM_Y + SHELF_Y                # -21.5 (= rail bottom)
RAIL_Y_MIN = SHELF_TOP_Y                            # -21.5
RAIL_Y_MAX = RAIL_Y_MIN + RAIL_LENGTH               # +28.5
HUB_TOP_Y = RAIL_Y_MAX + LEAD_IN_STRIP              # +36.5 (= HUB_Y / 2)

SHELF_Y_MAX = SHELF_TOP_Y                           # -21.5
SHELF_Y_MIN = HUB_BOTTOM_Y                          # -36.5

# Anchor holes through the hub (Ø 4mm)
ANCHOR_HOLE_DIAMETER = 4.0
# Top anchor is centered in the 8mm lead-in strip above the rail
ANCHOR_HOLE_TOP_Y = (RAIL_Y_MAX + HUB_TOP_Y) / 2    # +32.5
# Bottom anchor is centered in the shelf flange
ANCHOR_HOLE_BOT_Y = (SHELF_Y_MIN + SHELF_Y_MAX) / 2 # -29.0

# Golden scalars — captured via `make update-goldens`. Placeholders
# until the first capture run; the capture script overwrites these
# lines in place.
GOLDEN_VOLUME = 12934.5107
GOLDEN_BBOX = (40.0000, 73.0000, 11.0000)
GOLDEN_CENTROID = (0.0000, -1.1918, 3.3204)

# Tolerances
VOL_TOL = 1.0   # mm³ STL tessellation noise
DIM_TOL = 0.01  # mm


# ============================================================================
# Fixtures (module-scoped — build + export once)
# ============================================================================


@pytest.fixture(scope="module")
def bracket_mesh(tmp_path_factory) -> trimesh.Trimesh:
    tmp_dir = tmp_path_factory.mktemp("wall_bracket_mesh")
    stl_path = tmp_dir / "wall_bracket.stl"
    export_stl(build(), str(stl_path))
    mesh = trimesh.load(str(stl_path))
    mesh.merge_vertices()
    return mesh


# ============================================================================
# Group 1 — Golden scalar snapshots
# ============================================================================


class TestGoldenScalars:
    def test_volume(self, bracket_mesh):
        assert bracket_mesh.volume == pytest.approx(GOLDEN_VOLUME, abs=VOL_TOL)

    def test_bounding_box(self, bracket_mesh):
        extents = tuple(bracket_mesh.bounding_box.extents)
        assert extents == pytest.approx(GOLDEN_BBOX, abs=DIM_TOL)

    def test_centroid(self, bracket_mesh):
        centroid = tuple(bracket_mesh.centroid)
        assert centroid == pytest.approx(GOLDEN_CENTROID, abs=DIM_TOL)

    def test_single_body(self, bracket_mesh):
        assert bracket_mesh.body_count == 1


# ============================================================================
# Group 2 — Hub + shelf probes
# ============================================================================


class TestHubAndShelf:
    def test_hub_interior_is_solid(self, bracket_mesh):
        """Hub material exists across its XYZ extent away from the rail."""
        z_mid = HUB_Z / 2
        probes = [
            (-10.0, 0.0, z_mid),
            (10.0, 0.0, z_mid),
            (0.0, RAIL_Y_MIN + 5.0, z_mid),  # inside the rail area, away from rail profile
            (0.0, SHELF_Y_MIN + 5.0, z_mid),  # inside the shelf
            (-12.0, SHELF_Y_MIN + 2.0, z_mid),
            (12.0, SHELF_Y_MIN + 2.0, z_mid),
        ]
        assert_solid(bracket_mesh, probes, "hub interior")

    def test_shelf_is_solid_where_rail_would_be(self, bracket_mesh):
        """Shelf region (bottom 15mm) has NO rail feature — just hub material.

        Probes verify the shelf is solid (excluding the anchor hole) and
        that no rail protrudes above the hub front face in the shelf
        region.
        """
        # Solid shelf material — three probes off the anchor hole at
        # (0, SHELF_Y_MIN + SHELF_Y/2)
        assert_solid(
            bracket_mesh,
            [
                (8.0, SHELF_Y_MIN + SHELF_Y / 2, HUB_Z / 2),
                (-8.0, SHELF_Y_MIN + SHELF_Y / 2, HUB_Z / 2),
                (0.0, SHELF_Y_MIN + 3.0, HUB_Z / 2),
            ],
            "shelf hub material",
        )
        # Above the hub front face in the shelf region — empty (no rail here)
        assert_empty(
            bracket_mesh,
            [
                (0.0, SHELF_Y_MIN + 2.0, HUB_Z + 1.0),
                (0.0, SHELF_Y_MIN + SHELF_Y - 1.0, HUB_Z + 1.0),
            ],
            "no rail above shelf",
        )

    def test_no_residual_snap_features(self, bracket_mesh):
        """No material anywhere above Z = HUB_Z + RAIL_DEPTH (rail top).

        Catches regressions that reintroduce a snap bump, cantilever
        tongue, or any other feature above the rail top.
        """
        z_above_rail = HUB_Z + RAIL_DEPTH + 0.5
        probes = [
            (0.0, 0.0, z_above_rail),
            (0.0, 10.0, z_above_rail),
            (0.0, -10.0, z_above_rail),
            (-5.0, 0.0, z_above_rail),
            (5.0, 0.0, z_above_rail),
        ]
        assert_empty(bracket_mesh, probes, "above rail top")


# ============================================================================
# Group 3 — Rail dovetail profile
# ============================================================================


class TestRailProfile:
    def test_rail_interior_is_solid(self, bracket_mesh):
        """Material along the full rail length at mid-rail height."""
        z_mid = HUB_Z + RAIL_DEPTH / 2
        probes = [
            (0.0, RAIL_Y_MIN + 2.0, z_mid),
            (0.0, (RAIL_Y_MIN + RAIL_Y_MAX) / 2, z_mid),
            (0.0, RAIL_Y_MAX - 2.0, z_mid),
        ]
        assert_solid(bracket_mesh, probes, "rail interior")

    def test_rail_base_is_narrow(self, bracket_mesh):
        """Just outside RAIL_BASE_WIDTH near Z=HUB_Z is empty (undercut)."""
        z_near_base = HUB_Z + 0.3
        dx = 5.3  # outside base half-width (5.0), inside top half-width (5.5)
        probes = [
            (dx, (RAIL_Y_MIN + RAIL_Y_MAX) / 2, z_near_base),
            (-dx, (RAIL_Y_MIN + RAIL_Y_MAX) / 2, z_near_base),
        ]
        assert_empty(bracket_mesh, probes, "dovetail undercut at rail base")

    def test_rail_top_is_wide(self, bracket_mesh):
        """Just inside RAIL_TOP_WIDTH near the rail top is solid (wide top)."""
        z_near_top = HUB_Z + RAIL_DEPTH - 0.3
        dx = 5.2  # inside top half-width (5.5)
        probes = [
            (dx, (RAIL_Y_MIN + RAIL_Y_MAX) / 2, z_near_top),
            (-dx, (RAIL_Y_MIN + RAIL_Y_MAX) / 2, z_near_top),
        ]
        assert_solid(bracket_mesh, probes, "rail top width")


# ============================================================================
# Group 4 — Anchor holes
# ============================================================================


class TestAnchorHoles:
    def test_top_anchor_hole_is_open(self, bracket_mesh):
        """Top anchor hole passes through the hub at (0, ANCHOR_HOLE_TOP_Y)."""
        z_mid = HUB_Z / 2
        assert_empty(
            bracket_mesh,
            [(0.0, ANCHOR_HOLE_TOP_Y, z_mid)],
            "top anchor hole through hub",
        )

    def test_bottom_anchor_hole_is_open(self, bracket_mesh):
        """Bottom anchor hole passes through the shelf at (0, ANCHOR_HOLE_BOT_Y)."""
        z_mid = HUB_Z / 2
        assert_empty(
            bracket_mesh,
            [(0.0, ANCHOR_HOLE_BOT_Y, z_mid)],
            "bottom anchor hole through shelf",
        )

    def test_anchor_holes_are_local(self, bracket_mesh):
        """Hub is solid at XY values several mm away from each anchor hole."""
        z_mid = HUB_Z / 2
        probes = [
            (5.0, ANCHOR_HOLE_TOP_Y, z_mid),
            (-5.0, ANCHOR_HOLE_TOP_Y, z_mid),
            (5.0, ANCHOR_HOLE_BOT_Y, z_mid),
            (-5.0, ANCHOR_HOLE_BOT_Y, z_mid),
        ]
        assert_solid(bracket_mesh, probes, "hub solid away from anchor holes")


# ============================================================================
# Group 5 — Shelf flange (wider than upper hub)
# ============================================================================


class TestShelfFlange:
    """Shelf is wider than the upper hub — provides case-bottom support."""

    def test_flange_extends_past_upper_hub(self, bracket_mesh):
        """At X outside UPPER_HUB_X/2 but inside SHELF_X/2, the shelf is solid."""
        # 5mm overhang on each side: upper hub edge at X=15, shelf edge at X=20.
        # Probe at X=17.5 (middle of the overhang region).
        x_overhang = (UPPER_HUB_X / 2 + SHELF_X / 2) / 2  # 17.5
        z_mid = HUB_Z / 2
        y_mid = (SHELF_Y_MIN + SHELF_Y_MAX) / 2  # -29
        assert_solid(
            bracket_mesh,
            [(x_overhang, y_mid, z_mid), (-x_overhang, y_mid, z_mid)],
            "shelf flange overhang",
        )

    def test_upper_hub_is_not_wider_than_30mm(self, bracket_mesh):
        """Above the shelf top, X > UPPER_HUB_X/2 is empty (upper hub stops at 30mm)."""
        # Probe at X=17.5 (inside the flange's overhang region but
        # above the shelf Y range, at rail-level Y).
        x_overhang = (UPPER_HUB_X / 2 + SHELF_X / 2) / 2
        z_mid = HUB_Z / 2
        y_in_rail_region = (RAIL_Y_MIN + RAIL_Y_MAX) / 2
        assert_empty(
            bracket_mesh,
            [
                (x_overhang, y_in_rail_region, z_mid),
                (-x_overhang, y_in_rail_region, z_mid),
            ],
            "upper hub is not wider than 30mm",
        )

    def test_shelf_boundary_transition(self, bracket_mesh):
        """At the exact boundary Y=SHELF_TOP_Y, the flange overhang ends."""
        # Just below the shelf top: solid in the overhang
        x_overhang = (UPPER_HUB_X / 2 + SHELF_X / 2) / 2
        z_mid = HUB_Z / 2
        assert_solid(
            bracket_mesh,
            [(x_overhang, SHELF_TOP_Y - 1.0, z_mid)],
            "shelf flange just below top",
        )
        # Just above the shelf top: empty in the overhang region
        assert_empty(
            bracket_mesh,
            [(x_overhang, SHELF_TOP_Y + 1.0, z_mid)],
            "above shelf flange transition",
        )
