FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false

COPY ../pyproject.toml pyproject.toml

RUN poetry install --only main

COPY src src

WORKDIR /src

CMD uvicorn main:app \
    --host "0.0.0.0" \
    --port 8000 \
    --workers ${WORKERS} \
    --log-level ${LOG_LEVEL}
