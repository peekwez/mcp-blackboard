#!/bin/bash
set -e

echo ">> Installing python packages..."
uv sync --all-extras --all-packages --group dev --group infra
echo ">> Python packages installation complete!"
