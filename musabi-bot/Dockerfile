FROM python:3.9.15-buster

WORKDIR /app

COPY pyproject.toml poetry.lock setup.cfg ./
COPY musabi_bot/ ./musabi_bot/

RUN python -m pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT ["python3", "/app/musabi_bot/main.py"]
