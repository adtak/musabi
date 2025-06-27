.PHONY: format
format: black ruff

.PHONY: ruff
ruff:
				uv run ruff check src/* --no-cache --fix

.PHONY: mypy
mypy:
				uv run mypy .

.PHONY: test
test:
				uv run pytest
