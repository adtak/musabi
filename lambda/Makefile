.PHONY: format
format: black ruff

.PHONY: black
black:
				uv run black src/*

.PHONY: ruff
ruff:
				uv run ruff check src/* --no-cache --fix

.PHONY: mypy
mypy:
				uv run mypy .

.PHONY: test
test:
				uv run pytest
