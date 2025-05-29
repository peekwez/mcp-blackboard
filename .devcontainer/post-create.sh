#!/bin/bash
set -e

bash .devcontainer/scripts/add-dependencies.sh
bash .devcontainer/scripts/add-pre-commit-hooks.sh