.PHONY: help install install-dev test test-cov lint format typecheck clean build publish docs

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package
	pip install -e .

install-dev:  ## Install with dev dependencies
	pip install -e ".[dev,test]"
	pre-commit install

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=keyof --cov-report=term-missing --cov-report=html

lint:  ## Run linting
	ruff check src tests

format:  ## Format code
	ruff format src tests
	ruff check --fix src tests

typecheck:  ## Run type checking
	mypy src/keyof

check:  ## Run all checks (lint, typecheck, test)
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:  ## Build distribution packages
	python -m build

publish-test:  ## Publish to TestPyPI
	python -m twine upload --repository testpypi dist/*

publish:  ## Publish to PyPI
	python -m twine upload dist/*

docs:  ## Build documentation
	mkdocs build

docs-serve:  ## Serve documentation locally
	mkdocs serve
