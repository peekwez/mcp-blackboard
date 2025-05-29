#!/bin/bash
set -e

bash -i .devcontainer/scripts/add-dependencies.sh
bash -i .devcontainer/scripts/add-pre-commit-hooks.sh
