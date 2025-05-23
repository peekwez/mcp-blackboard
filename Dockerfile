FROM python:3.13-slim

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libavcodec-extra \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy local code to the container image.
COPY . /app

# Install pip dependencies
RUN --mount=type=cache,target=/var/cache/pip \
    pip install --upgrade pip \
    && pip install .


# Expose necessary port if any (MCP typically uses stdio, but if needed, uncomment below)
EXPOSE 8000

# Run the MCP Server
CMD ["python", "src/main.py"]