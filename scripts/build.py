"""Render parts to STL and STEP files in output/.

Usage:
    python scripts/build.py                  # build all projects
    python scripts/build.py esp-screen-case  # build one project
"""

import importlib
import pkgutil
import sys
from pathlib import Path

from build123d import export_step, export_stl

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "output"

# Map project directory names to their Python package names
PROJECTS: dict[str, str] = {
    "esp-screen-case": "esp_screen_case",
}


def discover_parts(package_name: str) -> list[str]:
    """Find all modules in a package that have a build() function."""
    package = importlib.import_module(package_name)
    parts = []
    for _importer, modname, _ispkg in pkgutil.iter_modules(package.__path__):
        if modname.startswith("_"):
            continue
        module = importlib.import_module(f"{package_name}.{modname}")
        if hasattr(module, "build"):
            parts.append(f"{package_name}.{modname}")
    return sorted(parts)


def build_and_export(module_path: str) -> bool:
    """Import a module, call build(), export STL + STEP. Returns True on success."""
    module = importlib.import_module(module_path)
    part_name = module_path.rsplit(".", 1)[-1]
    package_name = module_path.split(".")[0]

    print(f"  Building {part_name}...")
    part = module.build()

    project_output = OUTPUT_DIR / package_name
    project_output.mkdir(parents=True, exist_ok=True)

    stl_path = project_output / f"{part_name}.stl"
    step_path = project_output / f"{part_name}.step"

    export_stl(part, str(stl_path))
    export_step(part, str(step_path))

    print(f"    -> {stl_path}")
    print(f"    -> {step_path}")
    return True


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Filter to a single project if specified
    filter_project = sys.argv[1] if len(sys.argv) > 1 else None
    if filter_project and filter_project not in PROJECTS:
        print(f"Unknown project: {filter_project}")
        print(f"Available: {', '.join(PROJECTS)}")
        sys.exit(1)

    projects = {filter_project: PROJECTS[filter_project]} if filter_project else PROJECTS
    failed = False
    total = 0

    for project_dir, package_name in projects.items():
        print(f"\n[{project_dir}]")
        parts = discover_parts(package_name)

        if not parts:
            print("  No parts found.")
            continue

        for module_path in parts:
            try:
                build_and_export(module_path)
                total += 1
            except Exception as e:
                print(f"  FAIL {module_path}: {e}")
                failed = True

    print(f"\nBuilt {total} part(s).")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
