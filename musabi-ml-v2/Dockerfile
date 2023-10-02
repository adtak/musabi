FROM python:3.11.4-bullseye

RUN apt update && apt upgrade -y
ENV POETRY_HOME=/etc/poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "$POETRY_HOME/venv/bin:$PATH"
RUN mkdir ~/.fonts

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY musabi_ml/ ./musabi_ml/

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

ENTRYPOINT ["python3", "/app/musabi_ml/main.py"]
