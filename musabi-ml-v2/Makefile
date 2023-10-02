.PHONY: format
format: black ruff

.PHONY: black
black:
				poetry run black musabi_ml/*

.PHONY: ruff
ruff:
				poetry run ruff check musabi_ml/* --no-cache --fix

.PHONY: mypy
mypy:
				poetry run mypy .

.PHONY: test
test:
				poetry run pytest
