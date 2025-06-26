from unittest.mock import MagicMock

import pytest

from hooks_lib.aws_api import AWSApi


@pytest.fixture
def mock_botocore_config(mocker: MagicMock) -> MagicMock:
    """Mock BotocoreConfig."""
    return mocker.patch("hooks_lib.aws_api.BotocoreConfig")


@pytest.fixture
def mock_session(mocker: MagicMock) -> MagicMock:
    """Mock Session."""
    return mocker.patch("hooks_lib.aws_api.Session")


def test_aws_api_init(mock_session: MagicMock, mock_botocore_config: MagicMock) -> None:
    """Test AWSApi.__init__."""
    mock_session_instance = mock_session.return_value
    mock_config_instance = mock_botocore_config.return_value
    config_options = {"region_name": "us-east-1", "retries": {"max_attempts": 3}}

    api = AWSApi(config_options=config_options)

    mock_session.assert_called_once_with()
    assert api.session == mock_session_instance
    mock_botocore_config.assert_called_once_with(**config_options)
    assert api.config == mock_config_instance


@pytest.fixture
def aws_api(
    mock_session: MagicMock,
    mock_botocore_config: MagicMock,  # noqa: ARG001
) -> tuple[AWSApi, MagicMock]:
    """
    Fixture for AWSApi with mocked Session and BotocoreConfig.

    Returns the AWSApi instance and the session mock instance.
    """
    # The fixtures are automatically used, so patching is done.
    api = AWSApi(config_options={})
    return api, mock_session.return_value


def test_aws_api_ec2_client(aws_api: tuple[AWSApi, MagicMock]) -> None:
    """Test AWSApi.ec2_client property."""
    api, mock_session = aws_api
    client = api.ec2_client
    mock_session.client.assert_called_once_with("ec2", config=api.config)
    assert client == mock_session.client.return_value


def test_aws_api_kafka_client(aws_api: tuple[AWSApi, MagicMock]) -> None:
    """Test AWSApi.kafka_client property."""
    api, mock_session = aws_api
    client = api.kafka_client
    mock_session.client.assert_called_once_with("kafka", config=api.config)
    assert client == mock_session.client.return_value


@pytest.fixture
def mock_boto_client(mocker: MagicMock) -> MagicMock:
    """Fixture for a mocked boto3 client."""
    return mocker.MagicMock()


@pytest.fixture
def aws_api_with_mock_client(
    aws_api: tuple[AWSApi, MagicMock], mock_boto_client: MagicMock
) -> tuple[AWSApi, MagicMock]:
    """Fixture for AWSApi with a mocked client."""
    api, mock_session = aws_api
    mock_session.client.return_value = mock_boto_client
    return api, mock_boto_client


def test_get_subnets(aws_api_with_mock_client: tuple[AWSApi, MagicMock]) -> None:
    """Test AWSApi.get_subnets."""
    api, mock_client = aws_api_with_mock_client
    subnet_ids = ["subnet-1", "subnet-2"]
    expected_subnets = [{"SubnetId": "subnet-1"}, {"SubnetId": "subnet-2"}]
    mock_client.describe_subnets.return_value = {"Subnets": expected_subnets}

    subnets = api.get_subnets(subnets=subnet_ids)

    mock_client.describe_subnets.assert_called_once_with(SubnetIds=subnet_ids)
    assert subnets == expected_subnets


def test_get_security_groups(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    """Test AWSApi.get_security_groups."""
    api, mock_client = aws_api_with_mock_client
    sg_ids = ["sg-1", "sg-2"]
    expected_sgs = [{"GroupId": "sg-1"}, {"GroupId": "sg-2"}]
    mock_client.describe_security_groups.return_value = {"SecurityGroups": expected_sgs}

    sgs = api.get_security_groups(security_groups=sg_ids)

    mock_client.describe_security_groups.assert_called_once_with(GroupIds=sg_ids)
    assert sgs == expected_sgs


def test_get_kafka_versions(aws_api_with_mock_client: tuple[AWSApi, MagicMock]) -> None:
    """Test AWSApi.get_kafka_versions."""
    api, mock_client = aws_api_with_mock_client
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {"KafkaVersions": [{"Version": "2.8.1"}, {"Version": "3.6.0"}]},
        {"KafkaVersions": [{"Version": "3.7.0"}]},
    ]

    versions = api.get_kafka_versions()

    mock_client.get_paginator.assert_called_once_with("list_kafka_versions")
    mock_paginator.paginate.assert_called_once_with()
    assert versions == ["2.8.1", "3.6.0", "3.7.0"]


def test_get_kafka_versions_no_version_key(
    aws_api_with_mock_client: tuple[AWSApi, MagicMock],
) -> None:
    """Test AWSApi.get_kafka_versions when 'Version' key is missing."""
    api, mock_client = aws_api_with_mock_client
    mock_paginator = MagicMock()
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {"KafkaVersions": [{"Version": "2.8.1"}, {"NotVersion": "3.6.0"}]},
    ]

    versions = api.get_kafka_versions()

    assert versions == ["2.8.1"]
