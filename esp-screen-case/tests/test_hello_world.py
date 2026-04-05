"""Validate hello_world part geometry."""

import pytest

from esp_screen_case.hello_world import DEPTH, HEIGHT, WIDTH, build


def test_builds():
    """Part builds without error and returns a non-None result."""
    part = build()
    assert part is not None


def test_mesh_is_valid(export_and_load):
    """Exported STL has correct topology (Euler number 2, positive volume).

    Note: OCCT tessellation of filleted edges can produce non-manifold edges,
    so we check Euler number and volume rather than strict watertightness.
    The STEP export is the geometrically perfect source of truth.
    """
    part = build()
    mesh = export_and_load(part, "hello_world")
    assert mesh.euler_number == 2, f"Bad topology: Euler number is {mesh.euler_number}, expected 2"
    assert mesh.volume > 0, "Mesh has no volume"


def test_bounding_box(export_and_load):
    """Bounding box matches expected dimensions within tolerance."""
    part = build()
    mesh = export_and_load(part, "hello_world")
    extents = mesh.bounding_box.extents

    assert extents[0] == pytest.approx(WIDTH, abs=1.0)
    assert extents[1] == pytest.approx(DEPTH, abs=1.0)
    assert extents[2] == pytest.approx(HEIGHT, abs=1.0)


def test_has_positive_volume(export_and_load):
    """Part has non-trivial volume."""
    part = build()
    mesh = export_and_load(part, "hello_world")
    # A 40x30x20 box is 24000mm³; fillets reduce this slightly
    assert mesh.volume > 20000
