from __future__ import annotations

from typing import TYPE_CHECKING, Any

from boto3 import Session
from botocore.config import Config as BotocoreConfig

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.type_defs import SecurityGroupTypeDef, SubnetTypeDef
    from mypy_boto3_kafka.client import KafkaClient
    from mypy_boto3_kafka.type_defs import KafkaVersionTypeDef


class AWSApi:
    """AWS Api Class"""

    def __init__(self, config_options: Mapping[str, Any]) -> None:
        self.session = Session()
        self.config = BotocoreConfig(**config_options)

    @property
    def ec2_client(self) -> EC2Client:
        """Gets a boto EC2 client"""
        return self.session.client("ec2", config=self.config)

    @property
    def kafka_client(self) -> KafkaClient:
        """Gets a boto Kafka client"""
        return self.session.client("kafka", config=self.config)

    def get_subnets(self, subnets: Sequence[str]) -> list[SubnetTypeDef]:
        """Retrieve subnet list"""
        data = self.ec2_client.describe_subnets(
            SubnetIds=subnets,
        )
        return data["Subnets"]

    def get_security_groups(
        self, security_groups: Sequence[str]
    ) -> list[SecurityGroupTypeDef]:
        """Retrieve security group list"""
        data = self.ec2_client.describe_security_groups(
            GroupIds=security_groups,
        )
        return data["SecurityGroups"]

    def get_kafka_versions(self) -> list[str]:
        """Get available MSK Kafka versions"""
        versions_data: list[KafkaVersionTypeDef] = []
        for page in self.kafka_client.get_paginator("list_kafka_versions").paginate():
            versions_data += page["KafkaVersions"]
        return [v["Version"] for v in versions_data if "Version" in v]
