.PHONY: help build test sync clean

help:
	@echo "Targets:"
	@echo "  make sync    Install/update dependencies via uv"
	@echo "  make build   Render all parts to output/ (STL + STEP)"
	@echo "  make test    Run geometry validation tests"
	@echo "  make clean   Remove output/ directory"

sync:
	uv sync

build:
	uv run python scripts/build.py

test:
	uv run pytest

clean:
	rm -rf output
