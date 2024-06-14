.PHONY: format
format: black ruff

.PHONY: black
black:
				poetry run black melon_util/*

.PHONY: ruff
ruff:
				poetry run ruff check melon_util/* --no-cache --fix

.PHONY: mypy
mypy:
				poetry run mypy .
