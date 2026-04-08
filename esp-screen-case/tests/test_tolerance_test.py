"""Validate tolerance test piece geometry."""

from esp_screen_case.tolerance_test import build


def test_builds():
    """Part builds without error."""
    part = build()
    assert part is not None


def test_mesh_is_valid(export_and_load):
    """Exported STL has correct topology (2 bodies: rail half + channel half)."""
    part = build()
    mesh = export_and_load(part, "tolerance_test")
    # Two separate bodies (score gap), each with Euler 2
    assert mesh.body_count == 2, f"Expected 2 bodies, got {mesh.body_count}"
    assert mesh.volume > 0, "Mesh has no volume"


def test_fits_on_print_bed(export_and_load):
    """Part fits within the Centauri Carbon 2 build plate (256x256mm)."""
    part = build()
    mesh = export_and_load(part, "tolerance_test")
    extents = mesh.bounding_box.extents
    assert extents[0] < 256, f"Too wide: {extents[0]:.1f}mm"
    assert extents[1] < 256, f"Too deep: {extents[1]:.1f}mm"
    assert extents[2] < 256, f"Too tall: {extents[2]:.1f}mm"
