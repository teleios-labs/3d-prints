"""Capture golden scalar values for tolerance_test geometry tests.

Run after an intentional geometry change to refresh the EXPECTED block in
test_tolerance_test_geometry.py:

    uv run python esp-screen-case/tests/capture_tolerance_golden.py

Prints a ready-to-paste Python snippet to stdout.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import trimesh
from build123d import export_stl

# Allow running from repo root without install: add tests dir to path
sys.path.insert(0, str(Path(__file__).parent))

from esp_screen_case.tolerance_test import build  # noqa: E402
from geometry_helpers import split_bodies  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stl_path = Path(tmp) / "tolerance_test.stl"
        export_stl(build(), str(stl_path))
        mesh = trimesh.load(str(stl_path))
        mesh.merge_vertices()

        bodies = split_bodies(mesh)
        assert len(bodies) == 2, f"Expected 2 bodies, got {len(bodies)}"
        piece_a, piece_b = bodies

        print()
        print("# ============================================================")
        print("# Captured golden values — paste into test_tolerance_test_geometry.py")
        print("# ============================================================")
        print()
        print("GOLDEN_TOTAL_VOLUME = %.4f" % mesh.volume)
        print("GOLDEN_TOTAL_BBOX = (%.4f, %.4f, %.4f)" % tuple(mesh.bounding_box.extents))
        print()
        print("GOLDEN_A_VOLUME = %.4f" % piece_a.volume)
        print("GOLDEN_A_BBOX = (%.4f, %.4f, %.4f)" % tuple(piece_a.bounding_box.extents))
        print("GOLDEN_A_CENTROID_Y = %.4f" % piece_a.centroid[1])
        print()
        print("GOLDEN_B_VOLUME = %.4f" % piece_b.volume)
        print("GOLDEN_B_BBOX = (%.4f, %.4f, %.4f)" % tuple(piece_b.bounding_box.extents))
        print("GOLDEN_B_CENTROID_Y = %.4f" % piece_b.centroid[1])
        print()


if __name__ == "__main__":
    main()
