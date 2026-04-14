"""Geometry specification for case — refactor-safe tests."""

from __future__ import annotations

import pytest
import trimesh
from build123d import export_stl

from esp_screen_case.case import build
from geometry_helpers import assert_empty, assert_solid

# ============================================================================
# Expected geometry (spec — independent of dimensions.py)
# ============================================================================

# Board
BOARD_X = 181.26
BOARD_Y = 108.36

# Case exterior
WALL_THICKNESS = 2.0
BOARD_CLEARANCE = 0.3
EXTERIOR_X = BOARD_X + BOARD_CLEARANCE + 2 * WALL_THICKNESS   # 185.86
EXTERIOR_Y = BOARD_Y + BOARD_CLEARANCE + 2 * WALL_THICKNESS   # 112.96

# Z stack (z=0 at wall, increasing toward user)
Z_WALL = 0.0
Z_RECESS_FLOOR = 4.0
Z_CHANNEL_FLOOR = Z_RECESS_FLOOR + 7.3        # 11.3 — RAIL_DEPTH + 0.3 slop
Z_INTERIOR_FLOOR = Z_CHANNEL_FLOOR + 3.0      # 14.3
Z_STANDOFF_TOP = Z_INTERIOR_FLOOR + 8.0       # 22.3 — PCB back rests here
Z_CASE_TOP = Z_STANDOFF_TOP + 1.6 + 7.4       # 31.3 — flush with display glass

# Bracket recess
RECESS_X = 30.0
RECESS_Y = 67.0  # matches BRACKET_HUB_Y

# Dovetail channel (cut from recess floor)
CHANNEL_BASE_WIDTH = 10.2
CHANNEL_TOP_WIDTH = 11.2
CHANNEL_LENGTH = 50.0
# Channel runs vertically along case short axis. The recess is centered
# on the case; the channel is positioned inside the recess so the
# bottom of the channel opens at the recess's bottom edge.
RECESS_Y_MIN = -RECESS_Y / 2
RECESS_Y_MAX = RECESS_Y / 2
CHANNEL_Y_MIN = RECESS_Y_MIN
CHANNEL_Y_MAX = CHANNEL_Y_MIN + CHANNEL_LENGTH

# Standoffs — 4 corners, 3.2mm from each interior wall
HOLE_OFFSET = 3.2
BOARD_CORNER_X = BOARD_X / 2
BOARD_CORNER_Y = BOARD_Y / 2
STANDOFF_X = BOARD_CORNER_X - HOLE_OFFSET  # relative to case center
STANDOFF_Y = BOARD_CORNER_Y - HOLE_OFFSET
STANDOFF_OD = 6.0
STANDOFF_PILOT_DIAMETER = 2.5

# USB-C cutout — right wall, 2.18mm below center
USB_CENTER_Y = 52.0 - BOARD_Y / 2  # -2.18

# Golden placeholders
GOLDEN_VOLUME = 307673.2512
GOLDEN_BBOX = (185.5600, 112.6600, 31.3000)

VOL_TOL = 5.0
DIM_TOL = 0.05


# ============================================================================
# Fixture
# ============================================================================


@pytest.fixture(scope="module")
def case_mesh(tmp_path_factory) -> trimesh.Trimesh:
    tmp_dir = tmp_path_factory.mktemp("case_mesh")
    stl_path = tmp_dir / "case.stl"
    export_stl(build(), str(stl_path))
    mesh = trimesh.load(str(stl_path))
    mesh.merge_vertices()
    return mesh


# ============================================================================
# Goldens
# ============================================================================


class TestGoldenScalars:
    def test_volume(self, case_mesh):
        assert case_mesh.volume == pytest.approx(GOLDEN_VOLUME, abs=VOL_TOL)

    def test_bounding_box(self, case_mesh):
        extents = tuple(case_mesh.bounding_box.extents)
        assert extents == pytest.approx(GOLDEN_BBOX, abs=DIM_TOL)

    def test_single_body(self, case_mesh):
        assert case_mesh.body_count == 1


# ============================================================================
# Back plate + bracket recess
# ============================================================================


class TestBackPlateAndRecess:
    def test_back_plate_is_solid_outside_recess(self, case_mesh):
        """Back plate material exists where the recess isn't."""
        z = 2.0
        probes = [
            (-EXTERIOR_X / 2 + 5.0, 0.0, z),
            (EXTERIOR_X / 2 - 5.0, 0.0, z),
            (0.0, -EXTERIOR_Y / 2 + 5.0, z),
            (0.0, EXTERIOR_Y / 2 - 5.0, z),
        ]
        assert_solid(case_mesh, probes, "back plate outside recess")

    def test_recess_is_empty(self, case_mesh):
        """Bracket recess pocket is empty from z=0 to z=4, inside its XY footprint."""
        z = 2.0
        probes = [
            (-10.0, 0.0, z),
            (10.0, 0.0, z),
            (-10.0, -15.0, z),
            (10.0, 15.0, z),
        ]
        assert_empty(case_mesh, probes, "bracket recess pocket")

    def test_recess_walls_are_solid(self, case_mesh):
        """Just outside the recess footprint in X is solid back plate."""
        z = 2.0
        probes = [
            (-RECESS_X / 2 - 1.0, 0.0, z),
            (RECESS_X / 2 + 1.0, 0.0, z),
        ]
        assert_solid(case_mesh, probes, "recess outer walls")


# ============================================================================
# Dovetail channel inside the recess
# ============================================================================


class TestDovetailChannel:
    def test_channel_interior_is_empty(self, case_mesh):
        """Channel cavity is empty along its full length at mid-channel Z."""
        z_mid = (Z_RECESS_FLOOR + Z_CHANNEL_FLOOR) / 2  # 7.5
        y_positions = [
            CHANNEL_Y_MIN + 2.0,
            (CHANNEL_Y_MIN + CHANNEL_Y_MAX) / 2,
            CHANNEL_Y_MAX - 2.0,
        ]
        probes = [(0.0, y, z_mid) for y in y_positions]
        assert_empty(case_mesh, probes, "channel interior")

    def test_channel_has_dovetail_undercut(self, case_mesh):
        """Channel has a dovetail undercut — narrow opening at the
        recess floor, widening as it goes deeper into the case back.

        The channel matches the profile of the wall bracket's rail:
        the rail's narrow base lands at the recess floor (Z=4) and its
        wide top lands at the channel floor (Z=11), so the cavity in
        the case back is narrow at Z=4 and wide at Z=11.

        Half-widths:
            near recess floor (narrow):  CHANNEL_BASE_WIDTH / 2 = 5.1
            near channel floor (wide):   CHANNEL_TOP_WIDTH / 2 = 5.6

        Probes at dx=5.3 (outside narrow, inside wide):
          - near recess floor (narrow side): SOLID (outside the cavity)
          - near channel floor (wide side):  EMPTY (inside the cavity)
        """
        dx = 5.3
        y = (CHANNEL_Y_MIN + CHANNEL_Y_MAX) / 2

        # Just above the recess floor — channel is narrow here, probe is outside
        z_narrow = Z_RECESS_FLOOR + 0.3
        assert_solid(
            case_mesh,
            [(dx, y, z_narrow), (-dx, y, z_narrow)],
            "material beside channel narrow opening",
        )

        # Just below the channel floor — channel is wide here, probe is inside
        z_wide = Z_CHANNEL_FLOOR - 0.3
        assert_empty(
            case_mesh,
            [(dx, y, z_wide), (-dx, y, z_wide)],
            "inside channel wide cavity",
        )

    def test_channel_is_open_at_bottom_of_recess(self, case_mesh):
        """Channel is open at Y = CHANNEL_Y_MIN (recess bottom edge)."""
        z_mid = (Z_RECESS_FLOOR + Z_CHANNEL_FLOOR) / 2
        assert_empty(
            case_mesh,
            [(0.0, CHANNEL_Y_MIN + 0.5, z_mid)],
            "channel open at bottom",
        )

    def test_material_above_channel(self, case_mesh):
        """3mm of material exists between channel floor and interior floor."""
        z = (Z_CHANNEL_FLOOR + Z_INTERIOR_FLOOR) / 2  # 12.5
        y = (CHANNEL_Y_MIN + CHANNEL_Y_MAX) / 2
        assert_solid(case_mesh, [(0.0, y, z)], "material above channel")


# ============================================================================
# Interior floor + standoffs
# ============================================================================


class TestStandoffs:
    def test_interior_floor_is_solid(self, case_mesh):
        """Interior floor is solid between standoffs (no channel bleed-through)."""
        z = Z_INTERIOR_FLOOR - 0.3
        probes = [
            (30.0, 0.0, z),
            (-30.0, 0.0, z),
            (0.0, 30.0, z),  # Y outside the channel
            (0.0, -30.0, z),
        ]
        assert_solid(case_mesh, probes, "interior floor")

    def test_four_standoffs_present(self, case_mesh):
        """Standoffs exist at all 4 corners at their mid-height."""
        z = Z_INTERIOR_FLOOR + 4.0  # mid-standoff
        probes = [
            (STANDOFF_X, STANDOFF_Y, z),
            (-STANDOFF_X, STANDOFF_Y, z),
            (STANDOFF_X, -STANDOFF_Y, z),
            (-STANDOFF_X, -STANDOFF_Y, z),
        ]
        assert_solid(case_mesh, probes, "standoffs present at corners")

    def test_standoff_pilot_holes(self, case_mesh):
        """Self-tapping pilot hole at each standoff top."""
        z = Z_STANDOFF_TOP - 0.5
        probes = [
            (STANDOFF_X, STANDOFF_Y, z),
            (-STANDOFF_X, STANDOFF_Y, z),
            (STANDOFF_X, -STANDOFF_Y, z),
            (-STANDOFF_X, -STANDOFF_Y, z),
        ]
        assert_empty(case_mesh, probes, "standoff pilot holes")


# ============================================================================
# Side walls + USB-C cutout
# ============================================================================


class TestWallsAndUSB:
    def test_side_walls_are_solid(self, case_mesh):
        """Side walls exist at mid-interior-height, at all four sides."""
        z = Z_INTERIOR_FLOOR + 5.0
        probes = [
            (-EXTERIOR_X / 2 + 1.0, 0.0, z),
            (EXTERIOR_X / 2 - 1.0, 30.0, z),  # right wall clear of USB cutout
            (0.0, -EXTERIOR_Y / 2 + 1.0, z),
            (0.0, EXTERIOR_Y / 2 - 1.0, z),
        ]
        assert_solid(case_mesh, probes, "side walls")

    def test_usb_cutout_present(self, case_mesh):
        """Right wall has an opening at the USB-C Y position."""
        x = EXTERIOR_X / 2 - 1.0  # inside the right wall
        probes = [(x, USB_CENTER_Y, Z_STANDOFF_TOP + 0.8)]  # at PCB level
        assert_empty(case_mesh, probes, "USB-C cutout opening")

    def test_front_is_open(self, case_mesh):
        """No material spans the case front above the side walls."""
        z = Z_CASE_TOP + 1.0
        probes = [
            (0.0, 0.0, z),
            (30.0, 30.0, z),
            (-30.0, -30.0, z),
        ]
        assert_empty(case_mesh, probes, "open front")
