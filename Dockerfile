# syntax=docker/dockerfile:1.7

FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

COPY . /workspace

RUN python -m pip install --upgrade pip \
    && pip install -e '.[dev]'

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin bwdefend \
    && chown -R bwdefend:bwdefend /workspace

USER bwdefend

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["./scripts/linux-gate.sh"]
