# Named targets for the commands CONTRIBUTING.md documents. A thin layer: every recipe
# is exactly the line CI or the hook runs, with the same flags, so there is still one
# way to run each thing. Change the command in .github/workflows/ and here together.

.DEFAULT_GOAL := help
.PHONY: help install hooks check test all clean

help: ## List the targets
	@if [ -t 1 ]; then c='\033[36m'; r='\033[0m'; else c=''; r=''; fi; \
	grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' -v c="$$c" -v r="$$r" \
		'{ printf "  %s%-7s%s %s\n", c, $$1, r, $$2 }'

install: ## Install the dev tools from uv.lock
	uv sync --locked

hooks: ## Install the commit hook, once per clone
	uv run --locked pre-commit install

check: ## Run every hook over every tracked file, as checks.yml does
	uv run --locked pre-commit run --all-files --show-diff-on-failure

test: ## Run the test suite, as tests.yml does
	uv run --locked pytest

all: check test ## Run the checks, then the tests

clean: ## Remove the mypy, pytest, ruff and __pycache__ caches; keeps .venv
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -r {} +
