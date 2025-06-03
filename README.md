# External Resources MSK Module

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

External Resources module to provision and manage MSK instances in AWS with app-interface.

## Tech stack

* Terraform
* AWS provider
* Random provider
* Python 3.11
* Pydantic

## Development

Prepare your local development environment:

```bash
make dev
```

See the `Makefile` for more details.

## Debugging

To debug and run the module locally, run the following commands:

```bash
# Create the docker image
$ make build

# Get the input file from app-interface
qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider msk --identifier <MSK_IDENTIFIER> get-input > tmp/input.json

# Get the AWS credentials
$ vault login -method=oidc -address=https://vault.devshift.net
$ vault kv get \
    -mount app-sre/ \
    -field credentials \
    external-resources/<AWS_ACCOUNT_NAME> > tmp/credentials

# Run the module
$ docker run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    quay.io/redhat-services-prod/app-sre-tenant/er-aws-msk-main/er-aws-msk-main:$(git describe --tags)
```
