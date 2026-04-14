"""Validate wall bracket basic topology and print-bed fit."""

from esp_screen_case.dimensions import BOARD_HEIGHT
from esp_screen_case.wall_bracket import build


def test_builds():
    """Part builds without error."""
    part = build()
    assert part is not None


def test_mesh_is_valid(export_and_load):
    """Exported STL is a single closed solid."""
    part = build()
    mesh = export_and_load(part, "wall_bracket")
    assert mesh.body_count == 1, f"Expected 1 body, got {mesh.body_count}"
    assert mesh.volume > 0, "Mesh has no volume"


def test_fits_on_print_bed(export_and_load):
    """Bracket fits the Centauri Carbon 2 build plate (256x256mm)."""
    part = build()
    mesh = export_and_load(part, "wall_bracket")
    extents = mesh.bounding_box.extents
    assert extents[0] < 256, f"Too wide: {extents[0]:.1f}mm"
    assert extents[1] < 256, f"Too deep: {extents[1]:.1f}mm"
    assert extents[2] < 256, f"Too tall: {extents[2]:.1f}mm"


def test_bracket_hidden_behind_board(export_and_load):
    """Hub + rail footprint fits entirely behind the CrowPanel board."""
    part = build()
    mesh = export_and_load(part, "wall_bracket")
    extents = mesh.bounding_box.extents
    assert extents[1] < BOARD_HEIGHT, (
        f"Bracket taller than board: {extents[1]:.1f}mm > {BOARD_HEIGHT}mm"
    )
