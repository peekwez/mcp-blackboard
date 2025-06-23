FROM python:3.13-slim

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    --no-install-recommends curl ca-certificates


# Set working directory
WORKDIR /app

# Copy local code to the container image.
COPY . /app

ARG CUSTOM_SSL_CERTS=/usr/local/share/ca-certificates/cacert.pem
COPY certs/cacert.pem $CUSTOM_SSL_CERTS
RUN chmod 644 $CUSTOM_SSL_CERTS && update-ca-certificates

ENV SSL_CERT_FILE=$CUSTOM_SSL_CERTS
ENV REQUESTS_CA_BUNDLE=$CUSTOM_SSL_CERTS
ENV NODE_EXTRA_CA_CERTS=$CUSTOM_SSL_CERTS

# Install pip dependencies
RUN --mount=type=cache,target=/var/cache/pip \
    pip install --upgrade pip \
    && pip install -e .


# RUN uv pip install -e .
# Expose necessary port if any (MCP typically uses stdio, but if needed, uncomment below)
EXPOSE 8000

# Run the MCP Server
CMD ["nexus" , "run", "--host", "0.0.0.0", "--port", "8000"]
