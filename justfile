# bgee-ingest justfile

# Package directory
PKG := "src"

# Explicitly enumerate transforms (add new ingests here)
TRANSFORMS := "gene_to_expression"

# List all commands
_default:
    @just --list

# Initialize a new project
[group('project management')]
setup: _git-init install _git-add
    git commit -m "Initialize bgee-ingest"

# Install dependencies
[group('project management')]
install:
    uv sync --group dev

# Resolve BGEE_VERSION (highest FTP dir with data) and download
[group('ingest')]
download: install
    # Cache the resolved version so `metadata` sees the same value the
    # downloader actually used, even if the FTP listing changes mid-run.
    mkdir -p data
    uv run python scripts/resolve_bgee_version.py > data/.bgee-version
    BGEE_VERSION=$(cat data/.bgee-version) uv run downloader download.yaml

# Run all transforms
[group('ingest')]
transform-all: download
    #!/usr/bin/env bash
    set -euo pipefail
    for t in {{TRANSFORMS}}; do
        if [ -n "$t" ]; then
            echo "Transforming $t..."
            uv run koza transform {{PKG}}/$t.yaml
        fi
    done

# Emit output/release-metadata.yaml describing this build's upstream sources and artifacts
[group('ingest')]
metadata:
    BGEE_VERSION=$( [ -f data/.bgee-version ] && cat data/.bgee-version || uv run python scripts/resolve_bgee_version.py ) \
        uv run python scripts/write_metadata.py

# Run full pipeline: install, download, transform, metadata, test
[group('ingest')]
run: test transform-all metadata

# Run specific transform
[group('ingest')]
transform NAME:
    uv run koza transform {{PKG}}/{{NAME}}.yaml

# Run tests
[group('development')]
test: install
    uv run pytest

# Run tests with coverage
[group('development')]
test-cov: install
    uv run pytest --cov=. --cov-report=term-missing

# Lint code
[group('development')]
lint:
    uv run ruff check .

# Format code
[group('development')]
format:
    uv run ruff format .

# Clean output directory
[group('ingest')]
clean:
    rm -rf output/

# Hidden recipes
_git-init:
    git init

_git-add:
    git add .
