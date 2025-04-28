CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)

.PHONY: format
format:
	uv run ruff check
	uv run ruff format
	terraform fmt terraform

.PHONY: image_tests
image_tests:
	# hooks must be copied
	[ -d "hooks" ]

	# sources must be copied
	[ -d "$$TERRAFORM_MODULE_SRC_DIR" ]

	# test the terrform providers are downloaded
	[ -d "$$TF_PLUGIN_CACHE_DIR/registry.terraform.io/hashicorp/aws" ]

	# test all files in ./hooks are executable
	[ -z "$(shell for f in hooks/*; do [ ! -x "$$f" ] && [ "$$f" != "hooks/__init__.py" ] && echo not-executable; done)" ]

.PHONY: code_tests
code_tests:
	uv run ruff check --no-fix
	uv run ruff format --check
	terraform fmt -check=true "$$TERRAFORM_MODULE_SRC_DIR"
	uv run mypy
	uv run pytest -vv --cov=er_aws_msk --cov=hooks --cov-report=term-missing --cov-report xml

.PHONY: in_container_test
in_container_test: image_tests code_tests

.PHONY: test
test:
	$(CONTAINER_ENGINE) build --progress plain -t er-aws-msk:test .

.PHONY: build
build:
	$(CONTAINER_ENGINE) build --progress plain --target prod -t er-aws-msk:prod .

.PHONY: dev
dev:
	# Prepare local development environment
	uv sync

.PHONY: generate-variables-tf
generate-variables-tf:
	external-resources-io tf generate-variables-tf er_aws_msk.app_interface_input.AppInterfaceInput --output terraform/variables.tf

.PHONY: providers-lock
providers-lock:
	terraform -chdir=terraform providers lock -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_amd64 -platform=darwin_arm64
