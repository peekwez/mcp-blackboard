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

ARG CUSTOM_SSL_CERTS=/usr/local/share/ca-certificates/cacert.pem
COPY certs/cacert.pem $CUSTOM_SSL_CERTS
RUN chmod 644 $CUSTOM_SSL_CERTS
RUN update-ca-certificates

ENV SSL_CERT_FILE=$CUSTOM_SSL_CERTS
ENV REQUESTS_CA_BUNDLE=$CUSTOM_SSL_CERTS
ENV NODE_EXTRA_CA_CERTS=$CUSTOM_SSL_CERTS
ENV GIT_SSL_CAINFO=$CUSTOM_SSL_CERTS

COPY --from=uv --chown=vscode: /uv /uvx /bin/
