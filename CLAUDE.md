# 3d-prints

Monorepo for parametric 3D-printed parts. Each project is a Python package using build123d (OCCT kernel).

## Quick Start

```bash
uv sync                            # install all deps (installs Python if needed)
uv run python scripts/build.py     # render all parts to output/
uv run pytest                      # validate part geometry
```

## Structure

- Each project is a uv workspace member with its own `pyproject.toml` and src layout
- Parts are modules inside `src/<package>/` with a `build()` function returning a `Part`
- `scripts/build.py` discovers and renders all parts to `output/`
- Tests live in `<project>/tests/` and validate geometry (watertight, dimensions, volume)
- Never check generated STL/STEP into git — CI builds them as artifacts

## Adding a New Project

1. Create `my-project/pyproject.toml` with build123d dependency
2. Create `my-project/src/my_project/__init__.py`
3. Add part modules with `build()` functions
4. Add `"my-project"` to workspace members in root `pyproject.toml`
5. Add test path to `[tool.pytest.ini_options]` in root `pyproject.toml`
6. Run `uv sync` to pick up the new member

## Adding a Part to an Existing Project

1. Create `<project>/src/<package>/my_part.py` with a `build()` function
2. Create `<project>/tests/test_my_part.py` validating geometry
3. Run `uv run python scripts/build.py` to verify STL export
4. Run `uv run pytest` to verify tests pass

## Tooling

- **uv** — package manager, venv, Python version management
- **build123d** — parametric CAD (OCCT kernel)
- **trimesh** — mesh validation in tests
- **hatchling** — build backend
- **pytest** — test runner
