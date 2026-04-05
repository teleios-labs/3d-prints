"""Shared test fixtures for part validation."""

import pytest
import trimesh
from build123d import export_stl


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
