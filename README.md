# External Resources MSK Module

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

External Resources module to provision and manage MSK instances in AWS with app-interface.

## Tech stack

* Terraform CDKTF
* AWS provider
* Random provider
* Python 3.11
* Pydantic

## Debugging

To debug and run the module locally, run the following commands:

```bash
# Create the docker image
$ make build

# Get the input file from app-interface
qontract-cli --config=<CONFIG_PROD_TOML> external-resources get-input aws <AWS_ACCOUNT_NAME> msk <MKK_IDENTIFIER> > input.json

# Login to the destination AWS account
$ rh-aws-saml-login <AWS_ACCOUNT_NAME>

# Run the stack
$ docker run --rm -it --mount type=bind,source=$PWD/input.json,target=/inputs/input.json -e AWS_REGION=$AWS_REGION -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY  quay.io/app-sre/er-aws-msk:pre
```
