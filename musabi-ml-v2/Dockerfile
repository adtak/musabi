FROM python:3.11.4-bullseye

RUN apt update && apt upgrade -y
ENV POETRY_HOME=/etc/poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "$POETRY_HOME/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY musabi_ml/ ./musabi_ml/
COPY fonts/ ./fonts/

# RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT ["poetry", "run", "python", "/app/musabi_ml/main.py"]
