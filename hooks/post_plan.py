#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

from boto3 import Session
from botocore.config import Config as BotocoreConfig
from external_resources_io.config import Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging
from external_resources_io.terraform import (
    Action,
    ResourceChange,
    TerraformJsonPlanParser,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.type_defs import SecurityGroupTypeDef, SubnetTypeDef
    from mypy_boto3_kafka.client import KafkaClient
    from mypy_boto3_kafka.type_defs import KafkaVersionTypeDef

from er_aws_msk.app_interface_input import AppInterfaceInput

logger = logging.getLogger(__name__)

MIN_SUBNETS = 3


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
        """Get the subnet"""
        data = self.ec2_client.describe_subnets(
            SubnetIds=subnets,
        )
        return data["Subnets"]

    def get_security_groups(
        self, security_groups: Sequence[str]
    ) -> list[SecurityGroupTypeDef]:
        """Get the subnet"""
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


class MskPlanValidator:
    """The plan validator class"""

    def __init__(
        self, plan: TerraformJsonPlanParser, app_interface_input: AppInterfaceInput
    ) -> None:
        self.plan = plan
        self.input = app_interface_input
        self.aws_api = AWSApi(config_options={"region_name": self.input.data.region})
        self.errors: list[str] = []

    @property
    def msk_instance_updates(self) -> list[ResourceChange]:
        """Get the msk instance updates"""
        return [
            c
            for c in self.plan.plan.resource_changes
            if c.type == "aws_msk_cluster"
            and c.change
            and Action.ActionCreate in c.change.actions
        ]

    def _validate_subnets(self, subnets: Sequence[str]) -> str | None:
        logger.info(f"Validating subnets {subnets}")

        vpc_ids: set[str] = set()
        if len(subnets) < MIN_SUBNETS:
            self.errors.append("At least 3 subnets are required")
            return None

        data = self.aws_api.get_subnets(subnets)
        if missing := set(subnets).difference({s.get("SubnetId") for s in data}):
            self.errors.append(f"Subnet(s) {missing} not found")
            return None

        for subnet in data:
            if "VpcId" not in subnet:
                self.errors.append(
                    f"VpcId not found for subnet {subnet.get('SubnetId')}"
                )
                continue
            vpc_ids.add(subnet["VpcId"])
        if len(vpc_ids) > 1:
            self.errors.append("All subnets must belong to the same VPC")
        return vpc_ids.pop()

    def _validate_security_groups(
        self, security_groups: Sequence[str], vpc_id: str
    ) -> None:
        logger.info(f"Validating security group {security_groups}")
        data = self.aws_api.get_security_groups(security_groups)
        if missing := set(security_groups).difference({s.get("GroupId") for s in data}):
            self.errors.append(f"Security group(s) {missing} not found")
            return

        for sg in data:
            if sg.get("VpcId") != vpc_id:
                self.errors.append(
                    f"Security group {sg.get('GroupId')} does not belong to the same VPC as the subnets"
                )

    def _validate_kafka_version(self, kafka_version: str) -> None:
        logger.info(f"Validating kafka_version {kafka_version}")
        available_versions = self.aws_api.get_kafka_versions()
        if not available_versions:
            self.errors.append("Could not retrieve available Kafka versions from AWS.")
            return

        if kafka_version not in available_versions:
            self.errors.append(
                f"Invalid kafka_version: '{kafka_version}'. "
                f"Available versions are: {', '.join(available_versions)}"
            )

    def validate(self) -> bool:
        """Validate method"""
        for u in self.msk_instance_updates:
            if not u.change or not u.change.after:
                continue

            self._validate_kafka_version(kafka_version=u.change.after["kafka_version"])

            if vpc_id := self._validate_subnets(
                subnets=u.change.after["broker_node_group_info"][0]["client_subnets"]
            ):
                self._validate_security_groups(
                    security_groups=u.change.after["broker_node_group_info"][0][
                        "security_groups"
                    ],
                    vpc_id=vpc_id,
                )
        return not self.errors


if __name__ == "__main__":
    setup_logging()
    app_interface_input = parse_model(AppInterfaceInput, read_input_from_file())
    logger.info("Running MSK terraform plan validation")
    plan = TerraformJsonPlanParser(plan_path=Config().plan_file_json)
    validator = MskPlanValidator(plan, app_interface_input)
    if not validator.validate():
        logger.error(validator.errors)
        sys.exit(1)

    logger.info("Validation ended succesfully")
