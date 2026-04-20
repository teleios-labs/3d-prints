"""Capture golden scalar values for wall_bracket geometry tests.

Run after an intentional geometry change to refresh the golden constants
in ``test_wall_bracket_geometry.py``:

    uv run python esp-screen-case/tests/capture_wall_bracket_golden.py
    uv run python esp-screen-case/tests/capture_wall_bracket_golden.py --write
    make update-goldens  # equivalent to --write

Without ``--write``, the script prints captured values to stdout for
inspection. With ``--write`` (or via ``make update-goldens``), it
rewrites each ``GOLDEN_*`` assignment in the test file in place.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

import trimesh
from build123d import export_stl

# Allow running from repo root without install: add tests dir to path
sys.path.insert(0, str(Path(__file__).parent))

from esp_screen_case.wall_bracket import build  # noqa: E402

TEST_FILE = Path(__file__).parent / "test_wall_bracket_geometry.py"


def capture() -> dict[str, str]:
    """Build the wall_bracket part and return formatted golden values."""
    with tempfile.TemporaryDirectory() as tmp:
        stl_path = Path(tmp) / "wall_bracket.stl"
        export_stl(build(), str(stl_path))
        mesh = trimesh.load(str(stl_path))
        mesh.merge_vertices()

    def fmt_tuple(xyz) -> str:
        return "(%.4f, %.4f, %.4f)" % tuple(xyz)

    return {
        "GOLDEN_VOLUME": "%.4f" % mesh.volume,
        "GOLDEN_BBOX": fmt_tuple(mesh.bounding_box.extents),
        "GOLDEN_CENTROID": fmt_tuple(mesh.centroid),
    }


def print_values(values: dict[str, str]) -> None:
    print()
    print("# Captured golden values")
    print()
    for name, value in values.items():
        print(f"{name} = {value}")
    print()


def write_values(values: dict[str, str], path: Path) -> list[str]:
    """Rewrite each ``GOLDEN_* = ...`` line in ``path`` in place.

    Returns the list of names that actually changed (useful for CI
    diffing). Raises if any expected assignment is missing from the
    file — the goldens have to live somewhere.
    """
    text = path.read_text()
    changed: list[str] = []
    for name, new_value in values.items():
        pattern = re.compile(rf"^({re.escape(name)}\s*=\s*)(.*)$", re.MULTILINE)
        match = pattern.search(text)
        if not match:
            raise RuntimeError(f"{name} not found in {path}")
        if match.group(2).strip() != new_value:
            changed.append(name)
        text = pattern.sub(rf"\g<1>{new_value}", text, count=1)
    path.write_text(text)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--write",
        action="store_true",
        help="rewrite GOLDEN_* assignments in test_wall_bracket_geometry.py",
    )
    args = parser.parse_args()

    values = capture()

    if args.write:
        changed = write_values(values, TEST_FILE)
        if changed:
            print(f"Updated {len(changed)} golden(s) in {TEST_FILE.name}:")
            for name in changed:
                print(f"  {name} = {values[name]}")
        else:
            print(f"No changes — {TEST_FILE.name} goldens already current.")
    else:
        print_values(values)


if __name__ == "__main__":
    main()
