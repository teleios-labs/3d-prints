"""Validate wall bracket geometry."""

from esp_screen_case.wall_bracket import build
from esp_screen_case.dimensions import BOARD_HEIGHT


def test_builds():
    """Part builds without error."""
    part = build()
    assert part is not None


def test_mesh_is_valid(export_and_load):
    """Exported STL has correct topology."""
    part = build()
    mesh = export_and_load(part, "wall_bracket")
    assert mesh.euler_number == 2, f"Bad topology: Euler number is {mesh.euler_number}"
    assert mesh.volume > 0, "Mesh has no volume"


def test_fits_on_print_bed(export_and_load):
    """Bracket fits within 200x120x15mm — within Centauri Carbon 2 bed."""
    part = build()
    mesh = export_and_load(part, "wall_bracket")
    extents = mesh.bounding_box.extents
    assert extents[0] < 200, f"Too wide: {extents[0]:.1f}mm"
    assert extents[1] < 120, f"Too tall: {extents[1]:.1f}mm"
    assert extents[2] < 15, f"Too deep: {extents[2]:.1f}mm"


def test_bracket_narrower_than_board(export_and_load):
    """Bracket must be hidden behind the board — narrower than board height."""
    part = build()
    mesh = export_and_load(part, "wall_bracket")
    extents = mesh.bounding_box.extents
    assert extents[1] < BOARD_HEIGHT, f"Bracket taller than board: {extents[1]:.1f}mm > {BOARD_HEIGHT}mm"
