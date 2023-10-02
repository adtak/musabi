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

.PHONY: deploy
deploy: build tag push

.PHONY: build
build: 
				docker build -t generate-image-repository --platform linux/amd64 .

.PHONY: tag
tag:
				docker tag generate-image-repository:latest 589014808507.dkr.ecr.ap-northeast-1.amazonaws.com/generate-image-repository:latest

.PHONY: push
push:
				docker push 589014808507.dkr.ecr.ap-northeast-1.amazonaws.com/generate-image-repository:latest
