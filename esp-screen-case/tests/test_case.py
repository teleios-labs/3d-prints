"""Validate CrowPanel case basic topology and print-bed fit."""

from esp_screen_case.case import build
from esp_screen_case.dimensions import (
    BOARD_HEIGHT,
    BOARD_LENGTH,
    CASE_BOARD_CLEARANCE,
    CASE_WALL_THICKNESS,
)


def test_builds():
    part = build()
    assert part is not None


def test_mesh_is_valid(export_and_load):
    part = build()
    mesh = export_and_load(part, "case")
    assert mesh.body_count == 1, f"Expected 1 body, got {mesh.body_count}"
    assert mesh.volume > 0, "Mesh has no volume"


def test_fits_on_print_bed(export_and_load):
    part = build()
    mesh = export_and_load(part, "case")
    extents = mesh.bounding_box.extents
    assert extents[0] < 256, f"Too wide: {extents[0]:.1f}mm"
    assert extents[1] < 256, f"Too tall: {extents[1]:.1f}mm"
    assert extents[2] < 256, f"Too deep: {extents[2]:.1f}mm"


def test_exterior_matches_board_plus_clearance(export_and_load):
    """Exterior X and Y are board + clearance + 2*wall within 1mm."""
    part = build()
    mesh = export_and_load(part, "case")
    extents = mesh.bounding_box.extents
    expected_x = BOARD_LENGTH + CASE_BOARD_CLEARANCE + 2 * CASE_WALL_THICKNESS
    expected_y = BOARD_HEIGHT + CASE_BOARD_CLEARANCE + 2 * CASE_WALL_THICKNESS
    assert abs(extents[0] - expected_x) < 1.0, (
        f"X: got {extents[0]:.2f}, expected ~{expected_x:.2f}"
    )
    assert abs(extents[1] - expected_y) < 1.0, (
        f"Y: got {extents[1]:.2f}, expected ~{expected_y:.2f}"
    )
