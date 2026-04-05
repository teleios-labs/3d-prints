# 3d-prints

Parametric 3D-printed parts, built with [build123d](https://build123d.readthedocs.io/) (Python, OCCT kernel).

Monorepo managed with [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/).

## Setup

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/teleios-labs/3d-prints.git
cd 3d-prints
uv sync
```

## Build

Render all parts to STL + STEP:

```bash
uv run python scripts/build.py
```

Build a single project:

```bash
uv run python scripts/build.py esp-screen-case
```

Output lands in `output/`.

## Test

```bash
uv run pytest
```

## Projects

| Project | Description | Status |
|---------|-------------|--------|
| [esp-screen-case](esp-screen-case/) | Cases for Elecrow CrowPanel 7" displays | In progress |
