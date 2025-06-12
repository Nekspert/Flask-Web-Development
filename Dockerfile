FROM python:3.13-slim

ENV FLASK_APP=flasky.py
ENV FLASK_CONFIG=docker

ENV POETRY_VERSION=2.0.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR="/var/cache/poetry"

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

WORKDIR /home/flasky

COPY pyproject.toml poetry.lock ./
RUN python -m venv .venv
RUN poetry install && poetry add gunicorn

COPY Flasky/app app
COPY Flasky/migrations migrations
COPY Flasky/flasky.py flasky.py
COPY Flasky/config.py config.py
COPY Flasky/boot.sh boot.sh

# do boot.sh executable
RUN chmod a+x boot.sh

# runtime configuration
EXPOSE 5000
ENTRYPOINT ["./boot.sh"]