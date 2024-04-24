# syntax=docker/dockerfile:1
FROM python:3.9.17-slim as python-base

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    VIRTUAL_ENV="/venv"

ENV PATH="$POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH"

RUN python -m venv $VIRTUAL_ENV

WORKDIR /app
ENV PYTHONPATH="/app:$PYTHONPATH"

FROM python-base as builder-base
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    curl


RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /app
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --only main


FROM python-base as production
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $VIRTUAL_ENV $VIRTUAL_ENV

COPY . /app/
WORKDIR /app

CMD ["poetry", "run", "python", "bot.py"]