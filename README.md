# External Resources MSK Module

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

External Resources module to provision and manage MSK instances in AWS with app-interface.

## Tech stack

* Terraform
* AWS provider
* Random provider
* Python 3.12
* Pydantic

## Development

Prepare your local development environment:

```bash
make dev
```

See the `Makefile` for more details.

### Update Terraform modules

To update the Terraform modules used in this project, bump the version in [versions.tf](/terraform/versions.tf) and update the Terraform lockfile via:

```bash
make providers-lock
```

### Development workflow

1. Make changes to the code.
1. Build the image with `make build`.
1. Run the image manually with a proper  input file and credentials. See the [Debugging](#debugging) section below.
1. Please don't forget to remove (`-e ACTION=Destroy`) any development AWS resources you create, as they will incur costs.

## Debugging

To debug and run the module locally, run the following commands:

```bash
# Get the input file from app-interface
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider msk --identifier <MSK_IDENTIFIER> get-input > tmp/input.json

# Get the AWS credentials
$ qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider msk --identifier <MSK_IDENTIFIER> get-credentials > tmp/credentials

# Run the module
$ docker run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    --mount type=bind,source=$PWD/tmp/work,target=/work \
    -e DRY_RUN=True \
    -e ACTION=Apply \
    quay.io/redhat-services-prod/app-sre-tenant/er-aws-msk-main/er-aws-msk-main:latest
```
