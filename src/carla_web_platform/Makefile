.PHONY: format lint test run-platform

format:
	black app tests
	isort app tests

lint:
	ruff check app tests

test:
	pytest -q

run-platform:
	bash scripts/start_platform.sh
