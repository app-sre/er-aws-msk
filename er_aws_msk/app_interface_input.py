from collections.abc import Sequence
from typing import Any

from external_resources_io.input import AppInterfaceProvision
from pydantic import BaseModel


class MskClusterBrokerNodeGroupInfo(BaseModel):
    """aws_msk_cluster.broker_node_group_info"""

    client_subnets: Sequence[str]
    instance_type: str
    security_groups: Sequence[str]
    az_distribution: str = "DEFAULT"
    ebs_volume_size: int


class MskClusterClientAuthenticationSasl(BaseModel):
    """aws_msk_cluster.client_authentication.sasl"""

    iam: bool | None = None
    scram: bool | None = None


class MskClusterClientAuthentication(BaseModel):
    """aws_msk_cluster.client_authentication"""

    sasl: MskClusterClientAuthenticationSasl | None = None


class MskClusterLoggingInfoBrokerLogsCloudwatchLogs(BaseModel):
    """aws_msk_cluster.logging_info.broker_logs.cloudwatch_logs"""

    enabled: bool
    retention_in_days: int


class MskClusterLoggingInfoBrokerLogs(BaseModel):
    """aws_msk_cluster.logging_info.broker_logs"""

    cloudwatch_logs: MskClusterLoggingInfoBrokerLogsCloudwatchLogs | None = None


class MskClusterLoggingInfo(BaseModel):
    """aws_msk_cluster.logging_info"""

    broker_logs: MskClusterLoggingInfoBrokerLogs


class MskClusterOpenMonitoringPrometheusJmxExporter(BaseModel):
    """aws_msk_cluster.open_monitoring.prometheus.jmx_exporter"""

    enabled_in_broker: bool


class MskClusterOpenMonitoringPrometheusNodeExporter(BaseModel):
    """aws_msk_cluster.open_monitoring.prometheus.node_exporter"""

    enabled_in_broker: bool


class MskClusterOpenMonitoringPrometheus(BaseModel):
    """aws_msk_cluster.open_monitoring.prometheus"""

    jmx_exporter: MskClusterOpenMonitoringPrometheusJmxExporter | None = None
    node_exporter: MskClusterOpenMonitoringPrometheusNodeExporter | None = None


class MskClusterOpenMonitoring(BaseModel):
    """aws_msk_cluster.open_monitoring"""

    prometheus: MskClusterOpenMonitoringPrometheus


class MskData(BaseModel):
    """Data model for AWS MSK"""

    # app-interface
    region: str
    identifier: str
    output_resource_name: str | None = None
    output_prefix: str
    default_tags: Sequence[dict[str, Any]] | None = None
    scram_users: dict[str, dict[str, str]] | None = None

    # aws_msk_cluster
    broker_node_group_info: MskClusterBrokerNodeGroupInfo
    kafka_version: str
    number_of_broker_nodes: int
    client_authentication: MskClusterClientAuthentication | None = None
    logging_info: MskClusterLoggingInfo | None = None
    open_monitoring: MskClusterOpenMonitoring | None = None
    storage_mode: str | None = None
    tags: dict[str, str] | None = None

    # aws_msk_configuration
    server_properties: str


class AppInterfaceInput(BaseModel):
    """Input model for AWS MSK"""

    data: MskData
    provision: AppInterfaceProvision
