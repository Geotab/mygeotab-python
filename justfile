# justfile for mygeotab-python development tasks

# Install dependencies for development
install:
    uv sync --dev
    uv pip install -e .

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=mygeotab --cov-report=term-missing --cov-report=html

# Run linting
lint:
    uv run ruff check .

# Run linting and fix issues
lint-fix:
    uv run ruff check . --fix

# Format code
format:
    uv run ruff format .

# Run type checking
type-check:
    uv run mypy mygeotab

# Build the package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    find . -type d -name __pycache__ -delete
    find . -type f -name "*.pyc" -delete

# Run all checks (lint, format, type-check, test)
check: lint format type-check test

# Install pre-commit hooks (if using pre-commit)
setup-hooks:
    uv pip install pre-commit
    pre-commit install

# Update dependencies
update:
    uv sync --upgrade

# Show outdated dependencies
outdated:
    uv pip list --outdated

# Create a virtual environment
venv:
    uv venv

# Activate virtual environment (prints activation command)
activate:
    echo "Run: source .venv/bin/activate"

# Run the CLI tool
run-cli *args:
    uv run myg {{args}}
