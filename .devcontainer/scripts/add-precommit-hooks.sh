#!/bin/bash
set -e

echo ">> Install pre-commit hooks..."
uv run pre-commit install
uv run pre-commit autoupdate
echo ">> Pre-commit hooks installation complete!"
