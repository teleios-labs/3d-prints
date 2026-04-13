# 3d-prints

Monorepo for parametric 3D-printed parts. Each project is a Python package using build123d (OCCT kernel).

## Quick Start

```bash
make sync             # install/update deps via uv
make build            # render all parts to output/ (STL + STEP)
make test             # geometry validation tests
make update-goldens   # refresh tolerance_test golden scalars in place
make clean            # wipe output/
```

The Makefile is the preferred entrypoint — prefer it over raw `uv run` invocations in docs and PR bodies so the commands stay working when the script paths move.

## Structure

- Each project is a uv workspace member with its own `pyproject.toml` and src layout
- Parts are modules inside `src/<package>/` with a `build()` function returning a `Part`
- `scripts/build.py` discovers and renders all parts to `output/`
- Tests live in `<project>/tests/` and validate geometry (watertight, dimensions, volume)
- Never check generated STL/STEP/3mf into git — CI builds them as artifacts and `output/` is gitignored wholesale
- Never check large reference CAD files (`*.stp` / `*.step` source models) into the tree — keep them in a gitignored `reference/` directory per-project so `git clone` stays small

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

## build123d patterns & gotchas

### Prefer `Locations(Pos(...))` over nested `BuildPart(Pos(...), mode=...)`

To place a primitive at a specific location inside an outer `BuildPart`, use:

```python
with BuildPart() as result:
    Box(10, 10, 1)
    with Locations(Pos(20, 0, 0)):
        Box(5, 5, 1)
```

Not:

```python
with BuildPart() as result:
    Box(10, 10, 1)
    with BuildPart(Pos(20, 0, 0), mode=Mode.ADD):
        Box(5, 5, 1)
```

Both produce the same geometry, but the `Locations` form is shorter, doesn't create a throwaway sub-builder, and avoids the reuse footgun below. Matched pairs can share a single `Locations(Pos(l), Pos(r))` for one Box call.

### Nested `BuildPart` adds its final part to the parent on context exit

When `with BuildPart() as sub:` is inside another `BuildPart`, `sub.part` is added to the parent (in `Mode.ADD`) when the inner `with` block closes. This is intentional build123d behavior, **not** a leak.

The footgun: if you capture `sub.part` during construction to rotate/translate/otherwise manipulate it, then `add()` the transformed copy to the parent, the parent ends up with **both** the pre-transform copy (from the closure-add) and your transformed copy (from the explicit `add()`).

Rule: if you need a sub-part you'll manipulate before adding, build it **outside** the outer `BuildPart` so nothing is added on closure. Pattern:

```python
def _build_sub() -> Part:
    with BuildPart() as sub:
        Box(...)
    return sub.part  # fine — no enclosing builder to inherit it

def build() -> Part:
    transformed = _build_sub().rotate(Axis.X, 180).moved(Location((0, y, z)))
    with BuildPart() as result:
        Box(...)
        add(transformed)  # explicit, exactly once
    return result.part
```

### Print orientation ≠ assembly orientation

FDM bridges are poor-quality — sagging filament on the top side of cavities. If the critical fit surface of a part is the ceiling of a cut in assembly orientation, flip the part before exporting so that surface prints as near-vertical perimeters instead. In `tolerance_test.py`, piece B is built channel-down (assembly semantics) and then rotated 180° about X before joining the final assembly, so the solid roof lands on the build plate and the dovetail walls — the surfaces where the rail's undercut actually contacts — print as walls, not bridges.

Trade-off: the dovetail walls become a gentle inward overhang (angle = atan(Δwidth/2 / height)). Anything under ~45° from vertical is trivially printable without support. Compute the angle before committing to a flip.

### Watch for "swallowed" wedge/triangle cuts

If you build a compound cut by unioning a flat box with sloped wedges (e.g., ramps on a snap pocket), size the flat box to the **non-ramped** region only. A box that spans the full `catch + 2*ramp` length at full depth will contain the wedges as subsets and the wedges contribute nothing to the boolean. The pocket ends up flat-bottomed instead of ramped, and the defect is geometrically invisible until you probe mid-ramp.

## Testing parametric CAD

### Use a point-in-solid harness, not construction-style tests

`esp-screen-case/tests/geometry_helpers.py` exposes `assert_solid` / `assert_empty` that take a mesh and a list of `(x, y, z)` probes. Tests built on these validate the **final mesh** only — they don't care whether the part was built in builder mode, algebra mode, or raw OCCT, so any refactor that preserves geometry leaves them green.

Pattern for a new part:

1. Define an `EXPECTED` block at the top of the test module with named constants for each feature's expected coordinates. **Don't import these from `dimensions.py`** — they're a deliberate spec contract that should fail if the code silently changes a dimension.
2. Group tests by feature (`TestPieceA`, `TestPieceB`, `TestRailFitsInChannel`, …) and probe each feature's geometry directly.
3. Include golden-scalar tests (volume, bbox, centroid) for a coarse safety net.

### Don't encode private construction constants in test Z bounds

Boolean-robustness overshoots (small 0.05mm overlaps to keep OCCT happy at coincident faces) are private to the primitive's implementation. If a test constant is defined as `POCKET_Z_MIN = POCKET_Z_MAX - EXTRA - 0.05`, the `-0.05` silently couples the test to the primitive's internals and the tests drift when someone retunes the overshoot.

Instead: define the logical bound (`POCKET_Z_MAX - EXTRA`) and pick probe values with ≥0.1mm buffer from any boundary. The tests pass regardless of what overshoot the primitive currently uses.

### `make update-goldens` after intentional geometry changes

Golden volumes/bounding boxes/centroids will drift when you intentionally change a dimension or feature. Run `make update-goldens` — it runs the capture helper with `--write`, which does an in-place regex rewrite of each `GOLDEN_* = …` line in the test file and logs what changed. Idempotent when nothing moved.

One subtle point: the goldens are measured from the **exported STL** (trimesh volume), not from `part.volume` (OCCT exact volume). These can differ by ~0.03 mm³ from tessellation. Always use the capture helper rather than manually copying `part.volume` — the test fixture reads STL, so the goldens must match the STL.

## Git hygiene

- **Never commit** `output/` contents (STL/STEP/3mf), large source CAD files (`*.stp`), or slicer artifacts. `.gitignore` already covers all of these; don't work around it.
- Use `git push --force-with-lease` (not `--force`) when updating a PR branch after a rebase. It refuses to clobber new commits pushed by others.
- **Tolerance test workflow:** after any intentional geometry change, run `make build && make test`. If goldens fail with small (<1 mm³) differences, run `make update-goldens` and re-test. If they fail with large differences, the design actually moved and you should inspect the STL visually before refreshing.
