import pytest
from cdktf import Testing
from cdktf_cdktf_provider_aws.msk_cluster import (
    MskCluster,
)
from cdktf_cdktf_provider_aws.msk_configuration import MskConfiguration
from cdktf_cdktf_provider_aws.msk_scram_secret_association import (
    MskScramSecretAssociation,
)
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_random.provider import RandomProvider

from er_aws_msk.app_interface_input import AppInterfaceInput
from er_aws_msk.stack import MskStack as Stack


@pytest.fixture
def stack(ai_input: AppInterfaceInput) -> Stack:
    """Fixture to get the initialized stack."""
    return Stack(Testing.app(), "CDKTF", ai_input)


@pytest.fixture
def synthesized(stack: Stack) -> str:
    """Fixture to provide the synthesized stack."""
    return Testing.synth(stack)


@pytest.mark.parametrize(
    "provider_name",
    [
        AwsProvider.TF_RESOURCE_TYPE,
        RandomProvider.TF_RESOURCE_TYPE,
    ],
)
def test_stack_has_providers(synthesized: str, provider_name: str) -> None:
    """Test the stack has all the providers."""
    assert Testing.to_have_provider(synthesized, provider_name)


@pytest.mark.parametrize(
    "resource_name",
    [
        MskCluster.TF_RESOURCE_TYPE,
        MskConfiguration.TF_RESOURCE_TYPE,
        # sasl is enabled
        MskScramSecretAssociation.TF_RESOURCE_TYPE,
    ],
)
def test_stack_has_resources(synthesized: str, resource_name: str) -> None:
    """Test the stack has all the resources."""
    assert Testing.to_have_resource(synthesized, resource_name)


def test_stack_msk_config_id_and_name(synthesized: str, stack: Stack) -> None:
    """Test MskConfiguration has id and name based on kafka version."""
    assert Testing.to_have_resource_with_properties(
        synthesized,
        MskConfiguration.TF_RESOURCE_TYPE,
        {
            "kafka_versions": [
                "2.8.1",
            ],
            "lifecycle": {
                "create_before_destroy": True,
            },
            "name": "app-int-example-01-msk1-2-8-1",
        },
    )
    stack.node.find_child("app-int-example-01-msk1-2-8-1")
