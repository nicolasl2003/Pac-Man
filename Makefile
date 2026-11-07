LINT_FLAGS=--warn-return-any\
	   --warn-unused-ignores\
	   --ignore-missing-imports\
	   --disallow-untyped-defs\
	   --check-untyped-defs


run:
	@uv run python3 pac-man.py config.json

install:
	uv sync

debug:
	uv run python3 -m pudb pac-man.py config.json

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build
	rm -rf dist/*/_internal

fclean: clean
	rm -rf .venv
	rm -rf dist

lint:
	@status=0; \
	uv run find . -name "*.py" -not -path "*/.*" -exec flake8 {} + || status=1; \
	uv run mypy . $(LINT_FLAGS) || status=1; \
	exit $$status

lint-strict: LINT_FLAGS+=--strict
lint-strict: lint

build:
	uv run pyinstaller pac-man.py

.PHONY: run install debug clean lint lint-strict build
