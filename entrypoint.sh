#!/usr/bin/env bash
set -e

# Copy AWS credentials file to HOME/.aws/ if it exists
test -f /credentials && mkdir -p "${HOME}/.aws" && cp /credentials "${HOME}/.aws/credentials"

DRY_RUN=${DRY_RUN:-"True"}
ACTION=${ACTION:-"Apply"}

if [[ $DRY_RUN != "True" ]] && [[ $DRY_RUN != "False" ]]; then
    echo "Invalid DRY_RUN option: $DRY_RUN. Must be 'True' or 'False'"
    exit 1
fi

if [[ $ACTION != "Apply" ]] && [[ $ACTION != "Destroy" ]]; then
    echo "Invalid ACTION option: $ACTION. Must be 'Apply' or 'Destroy'"
    exit 1
fi

# CDKTF output options
export CI=true
export FORCE_COLOR=${FORCE_COLOR:-"0"}
export TF_CLI_ARGS=${TF_CLI_ARGS:-"-no-color"}

CDKTF_OUT_DIR="$HOME/cdktf.out/stacks/CDKTF"

# CDKTF init forces the provider re-download to calculate
# Other platform provider SHAs. USing terraform to init the configuration avoids it
# This shuold be reevaluated in the future.
# https://github.com/hashicorp/terraform-cdk/issues/3622
cdktf synth
terraform -chdir="$CDKTF_OUT_DIR" init

if [[ $ACTION == "Apply" ]]; then
    if [[ $DRY_RUN == "True" ]]; then
        cdktf plan --skip-synth
        if [ -f "validate_plan.py" ]; then
            terraform -chdir="$CDKTF_OUT_DIR" show -json "$CDKTF_OUT_DIR"/plan > "$CDKTF_OUT_DIR"/plan.json
            python3 validate_plan.py "$CDKTF_OUT_DIR"/plan.json
        fi
    elif [[ $DRY_RUN == "False" ]]; then
        cdktf apply \
            --skip-synth \
            --auto-approve \
            --outputs-file-include-sensitive-outputs=true \
            --outputs-file /work/output.json
    fi
elif [[ $ACTION == "Destroy" ]]; then
    if [[ $DRY_RUN == "True" ]]; then
        terraform -chdir="$CDKTF_OUT_DIR" plan -destroy
    elif [[ $DRY_RUN == "False" ]]; then
        cdktf destroy \
            --auto-approve
    fi
fi
