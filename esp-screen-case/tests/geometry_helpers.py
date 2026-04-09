"""Geometry-level assertion helpers for mesh-based tests.

These helpers operate on trimesh meshes only — they don't know or care how
the mesh was constructed (builder mode, algebra mode, BasePartObject, raw
OCCT). Tests built on top of these helpers are implementation-agnostic:
refactoring how a Part is built won't break them as long as the final
geometry is preserved.
"""

from __future__ import annotations

import numpy as np
import trimesh


def split_bodies(mesh: trimesh.Trimesh) -> list[trimesh.Trimesh]:
    """Split a mesh into disconnected solid bodies, sorted by centroid Y.

    The tolerance_test mesh has two separate solids (piece A at -Y, piece B
    at +Y) separated by a score gap. This returns them as a Y-sorted list so
    callers can reliably index by position.
    """
    bodies = mesh.split(only_watertight=False)
    return sorted(bodies, key=lambda b: b.centroid[1])


def assert_solid(
    mesh: trimesh.Trimesh,
    points: list[tuple[float, float, float]],
    label: str = "",
) -> None:
    """Assert every listed point is inside (solid material of) the mesh.

    Prints which specific point failed so test output points at the feature.
    """
    pts = np.asarray(points, dtype=float)
    contained = mesh.contains(pts)
    failures = [tuple(pts[i]) for i, ok in enumerate(contained) if not ok]
    if failures:
        prefix = f"[{label}] " if label else ""
        raise AssertionError(
            f"{prefix}expected SOLID at {len(failures)}/{len(pts)} point(s): "
            f"{failures}"
        )


def assert_empty(
    mesh: trimesh.Trimesh,
    points: list[tuple[float, float, float]],
    label: str = "",
) -> None:
    """Assert every listed point is outside (empty space of) the mesh.

    Prints which specific point failed so test output points at the feature.
    """
    pts = np.asarray(points, dtype=float)
    contained = mesh.contains(pts)
    failures = [tuple(pts[i]) for i, ok in enumerate(contained) if ok]
    if failures:
        prefix = f"[{label}] " if label else ""
        raise AssertionError(
            f"{prefix}expected EMPTY at {len(failures)}/{len(pts)} point(s): "
            f"{failures}"
        )
