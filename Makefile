install: ## Run `uv sync`
	uv sync
	uv sync --group test

lint:
	uv run isort --check .
	uv run black --check .
	uv run flake8 src tests

format: ## Formats you code with Black
	uv run isort .
	uv run black .

test:
	uv run pytest -v tests

publish:
	uv publish
