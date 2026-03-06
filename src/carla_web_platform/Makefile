.PHONY: format lint test run-platform run-api run-executor

format:
	black app tests
	isort app tests

lint:
	ruff check app tests

test:
	pytest -q

run-platform:
	bash run_platform.sh

run-api:
	bash scripts/start_api.sh

run-executor:
	bash scripts/start_executor.sh
