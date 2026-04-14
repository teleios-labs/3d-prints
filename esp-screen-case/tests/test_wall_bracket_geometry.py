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

# Hub (X = width, Y = height, Z = thickness from wall)
HUB_X = 30.0
HUB_Y = 67.0
HUB_Z = 4.0

# Dovetail rail on top of the hub front face
RAIL_BASE_WIDTH = 10.0       # narrow bottom — at hub front face (Z = HUB_Z)
RAIL_TOP_WIDTH = 11.0        # wider top (undercut) — at Z = HUB_Z + RAIL_DEPTH
RAIL_DEPTH = 7.0             # proud of the hub front face
RAIL_LENGTH = 50.0           # along Y (vertical in wall coordinates)

# Rail occupies the top 50mm of the 67mm hub, offset 2mm below the top
# for the lead-in chamfer strip. The bottom 15mm is the shelf.
LEAD_IN_STRIP = 2.0
SHELF_Y = 15.0
RAIL_Y_MAX = HUB_Y / 2 - LEAD_IN_STRIP              # 31.5
RAIL_Y_MIN = RAIL_Y_MAX - RAIL_LENGTH               # -18.5
SHELF_Y_MAX = RAIL_Y_MIN                            # -18.5
SHELF_Y_MIN = -HUB_Y / 2                            # -33.5

# Anchor holes through the hub (Ø 4mm)
ANCHOR_HOLE_DIAMETER = 4.0
# Top anchor is centered in the 2mm lead-in strip
ANCHOR_HOLE_TOP_Y = HUB_Y / 2 - LEAD_IN_STRIP / 2   # 32.5
# Bottom anchor is centered in the shelf
ANCHOR_HOLE_BOT_Y = (SHELF_Y_MIN + SHELF_Y_MAX) / 2 # -26.0

# Golden scalars — captured via `make update-goldens`. Placeholders
# until the first capture run; the capture script overwrites these
# lines in place.
GOLDEN_VOLUME = 11624.3307
GOLDEN_BBOX = (30.0000, 67.0000, 11.0000)
GOLDEN_CENTROID = (-0.0000, 0.9238, 3.5087)

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
