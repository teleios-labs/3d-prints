.PHONY: help build test sync clean update-goldens

help:
	@echo "Targets:"
	@echo "  make sync            Install/update dependencies via uv"
	@echo "  make build           Render all parts to output/ (STL + STEP)"
	@echo "  make test            Run geometry validation tests"
	@echo "  make update-goldens  Refresh tolerance_test golden scalars in place"
	@echo "  make clean           Remove output/ directory"

sync:
	uv sync

build:
	uv run python scripts/build.py

test:
	uv run pytest

update-goldens:
	uv run python esp-screen-case/tests/capture_tolerance_golden.py --write

clean:
	rm -rf output
