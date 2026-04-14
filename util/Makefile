.PHONY: format
format: black ruff

.PHONY: black
black:
			uv run black musabi_util/*

.PHONY: ruff
ruff:
			uv run ruff check musabi_util/* --no-cache --fix

.PHONY: mypy
mypy:
			uv run mypy .
