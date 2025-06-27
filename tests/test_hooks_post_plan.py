from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from external_resources_io.terraform import Action, ResourceChange

from er_aws_msk.app_interface_input import AppInterfaceInput
from hooks.post_plan import MskPlanValidator, TerraformJsonPlanParser


@pytest.fixture
def mock_terraform_plan_parser() -> MagicMock:
    """Mock TerraformJsonPlanParser for testing."""
    mock_plan = MagicMock()
    mock_plan.resource_changes = []
    parser = MagicMock(spec=TerraformJsonPlanParser)
    parser.plan = mock_plan
    return parser


@pytest.fixture
def mock_aws_api() -> Iterator[MagicMock]:
    """Mock AWSApi for testing."""
    with patch("hooks.post_plan.AWSApi") as mock:
        yield mock


def test_msk_plan_validator_validate_success(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test the full validate method with valid data."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    mock_aws_api.return_value.get_kafka_versions.return_value = ["2.8.1", "3.6.0"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_msk_cluster",
            change=MagicMock(
                after={
                    "kafka_version": "2.8.1",
                    "broker_node_group_info": [
                        {
                            "client_subnets": subnets,
                            "security_groups": security_groups,
                        }
                    ],
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = MskPlanValidator(mock_terraform_plan_parser, ai_input)
    assert validator.validate()
    assert not validator.errors


def test_msk_plan_validator_validate_failure_invalid_kafka_version(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure with an invalid Kafka version."""
    subnets = ["s1", "s2", "s3"]
    security_groups = ["sg1"]
    mock_aws_api.return_value.get_kafka_versions.return_value = ["2.8.1", "3.6.0"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_msk_cluster",
            change=MagicMock(
                after={
                    "kafka_version": "99.99.99",  # Invalid version
                    "broker_node_group_info": [
                        {
                            "client_subnets": subnets,
                            "security_groups": security_groups,
                        }
                    ],
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = MskPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "Invalid Kafka version" in validator.errors[0]


def test_msk_plan_validator_validate_failure_kafka_version_api_error(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test validation failure when Kafka version API call fails."""
    subnets = ["s1", "s2", "s3"]
    security_groups = ["sg1"]
    mock_aws_api.return_value.get_kafka_versions.return_value = []  # API failure
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_msk_cluster",
            change=MagicMock(
                after={
                    "kafka_version": "2.8.1",
                    "broker_node_group_info": [
                        {
                            "client_subnets": subnets,
                            "security_groups": security_groups,
                        }
                    ],
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = MskPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert (
        "Could not retrieve available Kafka versions from AWS." in validator.errors[0]
    )


def test_msk_plan_validator_validate_failure_subnet_count(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test the full validate method with insufficient subnet count."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
    ]  # Only 2 subnets
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    mock_aws_api.return_value.get_kafka_versions.return_value = ["2.8.1"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-123"} for sg in security_groups
    ]

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_msk_cluster",
            change=MagicMock(
                after={
                    "kafka_version": "2.8.1",
                    "broker_node_group_info": [
                        {
                            "client_subnets": subnets,
                            "security_groups": security_groups,
                        }
                    ],
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = MskPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert "At least 3 subnets are required" in validator.errors[0]


def test_msk_plan_validator_validate_failure_security_group_vpc(
    ai_input: AppInterfaceInput,
    mock_terraform_plan_parser: MagicMock,
    mock_aws_api: MagicMock,
) -> None:
    """Test the full validate method with security group in wrong VPC."""
    subnets = [
        "subnet-0a1b2c3d4e5f6a7b8",
        "subnet-0a1b2c3d4e5f6a7b9",
        "subnet-0a1b2c3d4e5f6a7c0",
    ]
    security_groups = ["sg-0a1b2c3d4e5f6a7b8"]
    mock_aws_api.return_value.get_kafka_versions.return_value = ["2.8.1"]
    mock_aws_api.return_value.get_subnets.return_value = [
        {"SubnetId": s, "VpcId": "vpc-123"} for s in subnets
    ]
    mock_aws_api.return_value.get_security_groups.return_value = [
        {"GroupId": sg, "VpcId": "vpc-456"} for sg in security_groups
    ]  # Wrong VPC

    mock_terraform_plan_parser.plan.resource_changes = [
        MagicMock(
            spec=ResourceChange,
            type="aws_msk_cluster",
            change=MagicMock(
                after={
                    "kafka_version": "2.8.1",
                    "broker_node_group_info": [
                        {
                            "client_subnets": subnets,
                            "security_groups": security_groups,
                        }
                    ],
                },
                actions=[Action.ActionCreate],
            ),
        )
    ]

    validator = MskPlanValidator(mock_terraform_plan_parser, ai_input)
    assert not validator.validate()
    assert len(validator.errors) == 1
    assert (
        f"Security group {security_groups[0]} does not belong to the same VPC as the subnets"
        in validator.errors[0]
    )
