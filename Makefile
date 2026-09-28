LINT_FLAGS=--warn-return-any\
	   --warn-unused-ignores\
	   --ignore-missing-imports\
	   --disallow-untyped-defs\
	   --check-untyped-defs


run:
	@uv run python3 -m src

install:
	uv sync

debug:
	uv run python3 -m pdb -m src

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

lint:
	uv run find . -name "*.py" -not -path "*/.*" -exec flake8 {} +
	uv run mypy . $(LINT_FLAGS)

lint-strict: LINT_FLAGS+=--strict
lint-strict: lint

.PHONY: run install debug clean lint lint-strict
