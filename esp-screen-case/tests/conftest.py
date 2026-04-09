"""Shared test fixtures for part validation."""

import pytest
import trimesh
from build123d import export_stl

from esp_screen_case.tolerance_test import build as build_tolerance_test


@pytest.fixture
def export_and_load(tmp_path):
    """Export a Part to STL and load it back as a trimesh for validation."""

    def _export_and_load(part, name: str = "test") -> trimesh.Trimesh:
        stl_path = tmp_path / f"{name}.stl"
        export_stl(part, str(stl_path))
        mesh = trimesh.load(str(stl_path))
        # BREP tessellation can produce minor gaps — merge duplicate vertices
        mesh.merge_vertices()
        return mesh

    return _export_and_load


@pytest.fixture(scope="module")
def tolerance_mesh(tmp_path_factory) -> trimesh.Trimesh:
    """Build tolerance_test once per test module and load as a trimesh.

    Module-scoped because building + exporting is expensive — sharing one
    mesh across all geometry tests keeps the suite fast.
    """
    tmp_dir = tmp_path_factory.mktemp("tolerance_mesh")
    stl_path = tmp_dir / "tolerance_test.stl"
    export_stl(build_tolerance_test(), str(stl_path))
    mesh = trimesh.load(str(stl_path))
    mesh.merge_vertices()
    return mesh


@pytest.fixture(scope="module")
def tolerance_bodies(tolerance_mesh) -> tuple[trimesh.Trimesh, trimesh.Trimesh]:
    """Return (piece_a, piece_b) — the rail half (-Y) and channel half (+Y)."""
    from geometry_helpers import split_bodies

    bodies = split_bodies(tolerance_mesh)
    assert len(bodies) == 2, f"Expected 2 disconnected bodies, got {len(bodies)}"
    return bodies[0], bodies[1]
