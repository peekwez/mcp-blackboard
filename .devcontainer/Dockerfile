# Use Python base image and install uv
ARG UV_VERSION=latest
ARG DEBIAN_VERSION=bookworm
ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

FROM mcr.microsoft.com/devcontainers/python:$PYTHON_VERSION-$DEBIAN_VERSION

# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv --chown=vscode: /uv /uvx /bin/
