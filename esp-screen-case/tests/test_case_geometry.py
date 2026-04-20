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
BOARD_X = 177.61
BOARD_Y = 104.16

# Case exterior
WALL_THICKNESS = 2.0
BOARD_CLEARANCE = 0.3
EXTERIOR_X = BOARD_X + BOARD_CLEARANCE + 2 * WALL_THICKNESS   # 181.91
EXTERIOR_Y = BOARD_Y + BOARD_CLEARANCE + 2 * WALL_THICKNESS   # 108.46

# Z stack (z=0 at wall, increasing toward user).
# Interior floor is now two-tier: low (Z=3) in most areas, high (Z=14.3)
# only in the thick strip that preserves the channel ceiling.
Z_WALL = 0.0
Z_RECESS_FLOOR = 4.0
Z_CHANNEL_FLOOR = Z_RECESS_FLOOR + 7.3        # 11.3 — RAIL_DEPTH + 0.3 slop
Z_INTERIOR_FLOOR_HIGH = Z_CHANNEL_FLOOR + 3.0 # 14.3 — above channel
Z_INTERIOR_FLOOR_LOW = 3.0                    # elsewhere
Z_STANDOFF_TOP = Z_INTERIOR_FLOOR_LOW + 19.0  # 22 — PCB back rests here
Z_CASE_TOP = Z_STANDOFF_TOP + 1.6 + 7.4       # 31 — flush with display glass

# Alias for backward compatibility — most probe tests want the floor at the
# standoff corners, which is the low (thin) floor.
Z_INTERIOR_FLOOR = Z_INTERIOR_FLOOR_LOW

# Thick strip down the middle — preserves the channel ceiling
CASE_THICK_STRIP_HALF_WIDTH = 6.6

# Bracket recess — opens at the case's bottom exterior edge so the
# bracket hub can slide up into it from below.
RECESS_X = 30.0
RECESS_Y = 58.0  # rail length 50 + lead-in 8

# Dovetail channel (cut from recess floor)
CHANNEL_BASE_WIDTH = 10.2
CHANNEL_TOP_WIDTH = 11.2
CHANNEL_LENGTH = 50.0

# Both recess and channel have their bottom edges at the case bottom.
RECESS_Y_MIN = -EXTERIOR_Y / 2                       # -54.23
RECESS_Y_MAX = RECESS_Y_MIN + RECESS_Y               # +3.77
RECESS_Y_CENTER = (RECESS_Y_MIN + RECESS_Y_MAX) / 2  # -25.23
CHANNEL_Y_MIN = RECESS_Y_MIN                         # -54.23
CHANNEL_Y_MAX = CHANNEL_Y_MIN + CHANNEL_LENGTH       # -4.23

# Standoffs — 4 corners, 3.2mm from each interior wall
HOLE_OFFSET = 3.2
BOARD_CORNER_X = BOARD_X / 2
BOARD_CORNER_Y = BOARD_Y / 2
STANDOFF_X = BOARD_CORNER_X - HOLE_OFFSET  # relative to case center
STANDOFF_Y = BOARD_CORNER_Y - HOLE_OFFSET
STANDOFF_OD = 6.0
STANDOFF_PILOT_DIAMETER = 2.5

# USB-C cutout — right wall, 2.18mm below center
USB_CENTER_Y = 51.22 - BOARD_Y / 2  # -0.86

# Golden placeholders
GOLDEN_VOLUME = 98891.5375
GOLDEN_BBOX = (181.9100, 108.4600, 31.0000)

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
        """Back plate material exists where the recess isn't.

        The recess now spans Y=[-54.23, +3.77] (bottom-aligned) and
        X=[-15, +15]. Probes outside these ranges should land in solid
        back plate material.
        """
        z = 2.0
        probes = [
            # Near left wall (outside recess X)
            (-EXTERIOR_X / 2 + 5.0, 0.0, z),
            # Near right wall (outside recess X)
            (EXTERIOR_X / 2 - 5.0, 0.0, z),
            # Above the recess (Y > RECESS_Y_MAX = +1.67)
            (0.0, 30.0, z),
            # Outside the recess X footprint but inside the recess Y range:
            # X=25 > 15 (outside recess X), Y=-30 inside recess Y range
            (25.0, -30.0, z),
        ]
        assert_solid(case_mesh, probes, "back plate outside recess")

    def test_recess_is_empty(self, case_mesh):
        """Bracket recess pocket is empty from z=0 to z=4, inside its XY footprint."""
        z = 2.0
        # Recess X=[-15, +15], Y=[-54.23, +3.77]. Probes inside this
        # footprint but avoiding the channel X extent (~[-5.6, +5.6])
        # which is also empty for a different reason.
        probes = [
            (-10.0, -10.0, z),
            (10.0, -10.0, z),
            (-10.0, -40.0, z),
            (10.0, -40.0, z),
            (0.0, -50.0, z),   # near the case bottom, still inside recess
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
        """3mm of material exists between channel floor and the high interior floor."""
        z = (Z_CHANNEL_FLOOR + Z_INTERIOR_FLOOR_HIGH) / 2  # 12.8 — inside thick strip
        y = (CHANNEL_Y_MIN + CHANNEL_Y_MAX) / 2
        assert_solid(case_mesh, [(0.0, y, z)], "material above channel")


# ============================================================================
# Interior floor + standoffs
# ============================================================================


class TestStandoffs:
    def test_interior_floor_is_solid(self, case_mesh):
        """Interior floor is solid between standoffs (no channel bleed-through)."""
        # Probe at Z just below Z_INTERIOR_FLOOR_LOW (3.0): should be
        # solid back-plate material since the thin floor has the cavity
        # above it. Probes must be outside the bracket recess XY footprint
        # (recess covers X=[-15,+15] for its Y range) and outside the
        # channel (X=[-5.6,+5.6]) — use X=30 to stay in the thin region.
        z = Z_INTERIOR_FLOOR_LOW - 0.3  # 2.7
        probes = [
            (30.0, 0.0, z),
            (-30.0, 0.0, z),
            (30.0, 30.0, z),   # well outside recess/channel in both X and Y
            (-30.0, -30.0, z),
        ]
        assert_solid(case_mesh, probes, "interior floor (thin)")

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

    def test_thin_back_plate_has_cavity_above(self, case_mesh):
        """Outside the thick strip, the case back is only 3mm thick —
        the interior cavity extends all the way down to Z=3."""
        # Probe at Z=5 (above the thin floor but below the thick floor),
        # well outside the thick strip in X — should be empty (cavity).
        x = CASE_THICK_STRIP_HALF_WIDTH + 5.0  # 11.6
        probes = [
            (x, 0.0, 5.0),
            (-x, 0.0, 5.0),
            (x, 30.0, 10.0),
            (-x, -30.0, 10.0),
        ]
        assert_empty(case_mesh, probes, "thin back plate cavity")


# ============================================================================
# Side walls + USB-C cutout
# ============================================================================


class TestWallsAndUSB:
    def test_side_walls_are_solid(self, case_mesh):
        """Side walls exist at mid-interior-height, at all four sides.

        Use Z_STANDOFF_TOP - 2.0 (= 20.0) which is above the channel
        ceiling (11.3) and above the step, so all four wall probes land
        in solid material regardless of the two-tier floor.
        """
        z = Z_STANDOFF_TOP - 2.0  # 20.0 — above channel, within side walls
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
