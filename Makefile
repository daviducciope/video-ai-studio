SHELL := /bin/bash

.PHONY: setup dev web api worker test

setup:
	./scripts/setup.sh

dev:
	./scripts/dev.sh

web:
	./scripts/run_web.sh

api:
	./scripts/run_api.sh

worker:
	./scripts/run_worker.sh

test:
	PYTHONPATH=services/api:packages/shared ./.venv/bin/pytest services/api/tests
	PYTHONPATH=services/worker:packages/shared ./.venv/bin/pytest services/worker/tests
