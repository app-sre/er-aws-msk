CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)

.PHONY: format
format:
	uv run ruff check
	uv run ruff format


.PHONY: test
test:
	# test /tmp is empty
	[ -z "$(shell ls -A /tmp)" ]
	unset UV_FROZEN && uv lock --locked
	uv run ruff check --no-fix
	uv run ruff format --check
	uv run mypy
	uv run pytest -vv --cov=er_aws_msk --cov-report=term-missing --cov-report xml
	[ -f "validate_plan.py" ]

.PHONY: build
build:
	$(CONTAINER_ENGINE) build -t er-aws-msk:test .
