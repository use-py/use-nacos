install: ## Run `poetry install`
	poetry install --no-root

lint:
	poetry run isort --check .
	poetry run black --check .
	poetry run flake8 src tests

format: ## Formats you code with Black
	poetry run isort .
	poetry run black .

run: ## run `poetry run use-nacos`
	poetry run use-nacos


test:
	poetry run pytest -v tests

publish:
	poetry publish --build