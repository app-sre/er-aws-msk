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
qontract-cli --config=<CONFIG_TOML> external-resources --provisioner <AWS_ACCOUNT_NAME> --provider msk --identifier <MSK_IDENTIFIER> get-input > tmp/input.json

# Get the AWS credentials
$ vault login -method=oidc -address=https://vault.devshift.net
$ vault kv get \
    -mount app-sre/ \
    -field credentials \
    external-resources/<AWS_ACCOUNT_NAME> > tmp/credentials

# Run the stack
$ docker run --rm -it \
    --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json \
    --mount type=bind,source=$PWD/tmp/credentials,target=/credentials \
    quay.io/app-sre/er-aws-msk:$(git describe --tags)
```

Get the stack file:

```bash
$ docker rm -f erv2 && docker run --name erv2 --mount type=bind,source=$PWD/tmp/input.json,target=/inputs/input.json --mount type=bind,source=$PWD/tmp/credentials,target=/credentials -e AWS_SHARED_CREDENTIALS_FILE=/credentials --entrypoint cdktf quay.io/app-sre/er-aws-msk:$(git describe --tags) synth --output /tmp/cdktf.out

docker cp erv2:/tmp/cdktf.out/stacks/CDKTF/cdk.tf.json tmp/cdk.tf.json
```

Compile the plan:

```bash
cd tmp/...
terraform init
terraform plan -out=plan.out
terraform show -json plan.out > plan.json
```

Run the validation:

```bash
export ER_INPUT_FILE=$PWD/tmp/input.json
export AWS_SHARED_CREDENTIALS_FILE=$PWD/tmp/credentials
python validate_plan.py tmp/plan.json
```
