import pytest
from cdktf import Testing
from external_resources_io.input import parse_model

from er_aws_msk.app_interface_input import AppInterfaceInput

Testing.__test__ = False


@pytest.fixture
def raw_input_data() -> dict:
    """Fixture to provide test data for the AppInterfaceInput."""
    return {
        "data": {
            "kafka_version": "2.8.1",
            "number_of_broker_nodes": 3,
            "broker_node_group_info": {
                "instance_type": "kafka.t3.small",
                "client_subnets": [
                    "subnet-A",
                    "subnet-B",
                    "subnet-C",
                ],
                "security_groups": ["sg-id"],
                "ebs_volume_size": 1,
            },
            "server_properties": "auto.create.topics.enable=false\ndefault.replication.factor=3\nmin.insync.replicas=2\nnum.io.threads=8\nnum.network.threads=5\nnum.partitions=1\nnum.replica.fetchers=2\nreplica.lag.time.max.ms=30000\nsocket.receive.buffer.bytes=102400\nsocket.request.max.bytes=104857600\nsocket.send.buffer.bytes=102400\nunclean.leader.election.enable=true\nzookeeper.session.timeout.ms=18000\nallow.everyone.if.no.acl.found=false\n",
            "logging_info": {
                "broker_logs": {
                    "cloudwatch_logs": {"enabled": True, "retention_in_days": 1},
                },
            },
            "client_authentication": {"sasl": {"scram": True}},
            "identifier": "app-int-example-01-msk1",
            "output_resource_name": "creds-msk1",
            "output_prefix": "app-int-example-01-msk1-msk",
            "scram_users": {
                "user1-0": {
                    "password": "not-a-real-password",
                    "username": "user1",
                },
                "user2-0": {
                    "password": "not-a-real-password",
                    "username": "user2",
                },
            },
            "tags": {
                "managed_by_integration": "external_resources",
                "cluster": "appint-ex-01",
                "namespace": "example-msk-01",
                "environment": "production",
                "app": "msk-example",
            },
            "default_tags": [{"tags": {"app": "app-sre-infra"}}],
            "region": "us-east-1",
        },
        "provision": {
            "provision_provider": "aws",
            "provisioner": "app-int-example-01",
            "provider": "msk",
            "identifier": "app-int-example-01-msk1",
            "target_cluster": "appint-ex-01",
            "target_namespace": "example-msk-01",
            "target_secret_name": "creds-msk1",
            "module_provision_data": {
                "tf_state_bucket": "external-resources-terraform-state-dev",
                "tf_state_region": "us-east-1",
                "tf_state_dynamodb_table": "external-resources-terraform-lock",
                "tf_state_key": "aws/app-int-example-01/msk/app-int-example-01-msk1/terraform.tfstate",
            },
        },
    }


@pytest.fixture
def ai_input(raw_input_data: dict) -> AppInterfaceInput:
    """Fixture to provide the AppInterfaceInput."""
    return parse_model(AppInterfaceInput, raw_input_data)
