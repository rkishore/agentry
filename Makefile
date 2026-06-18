.PHONY: install lint typecheck test boundaries slice

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest

boundaries:
	uv run lint-imports

slice:
	uv run python -m agentry.entrypoints.cli ingest tests/fixtures
	uv run python -m agentry.entrypoints.cli query "$$(uv run python -c 'import json; print(json.load(open("tests/fixtures/eval.json"))["question"])')"
	uv run python -m agentry.entrypoints.cli eval tests/fixtures/eval.json
