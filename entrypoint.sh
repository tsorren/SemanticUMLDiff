#!/bin/bash
set -e

BASE_UML_DIR=$1
PR_UML_DIR=$2
GITHUB_TOKEN=$3

# Run the CLI
# Using PYTHONPATH to ensure the src directory is in the path
PYTHONPATH=/app python -m src.cli.main --base "$BASE_UML_DIR" --pr "$PR_UML_DIR" --token "$GITHUB_TOKEN"
