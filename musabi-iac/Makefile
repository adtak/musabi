.PHONY: format black isort test deploy destroy

format: black isort

black:
				poetry run black . --preview

isort:
				poetry run isort .

mypy:
				poetry run mypy .

test:
				poetry run pytest

deploy:
				poetry run cdk deploy --all

destroy:
				poetry run cdk destroy --all
