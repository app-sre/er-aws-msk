import json

from cdktf import S3Backend, TerraformOutput, TerraformStack
from cdktf_cdktf_provider_aws.cloudwatch_log_group import CloudwatchLogGroup
from cdktf_cdktf_provider_aws.kms_alias import KmsAlias
from cdktf_cdktf_provider_aws.kms_key import KmsKey
from cdktf_cdktf_provider_aws.msk_cluster import (
    MskCluster,
    MskClusterBrokerNodeGroupInfo,
    MskClusterBrokerNodeGroupInfoStorageInfo,
    MskClusterBrokerNodeGroupInfoStorageInfoEbsStorageInfo,
    MskClusterClientAuthentication,
    MskClusterClientAuthenticationSasl,
    MskClusterConfigurationInfo,
    MskClusterLoggingInfo,
    MskClusterLoggingInfoBrokerLogs,
    MskClusterLoggingInfoBrokerLogsCloudwatchLogs,
    MskClusterOpenMonitoring,
    MskClusterOpenMonitoringPrometheus,
    MskClusterOpenMonitoringPrometheusJmxExporter,
    MskClusterOpenMonitoringPrometheusNodeExporter,
)
from cdktf_cdktf_provider_aws.msk_configuration import MskConfiguration
from cdktf_cdktf_provider_aws.msk_scram_secret_association import (
    MskScramSecretAssociation,
)
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.secretsmanager_secret import SecretsmanagerSecret
from cdktf_cdktf_provider_aws.secretsmanager_secret_policy import (
    SecretsmanagerSecretPolicy,
)
from cdktf_cdktf_provider_aws.secretsmanager_secret_version import (
    SecretsmanagerSecretVersion,
)
from cdktf_cdktf_provider_random.provider import RandomProvider
from constructs import Construct

from .app_interface_input import AppInterfaceInput


class MskStack(TerraformStack):
    """AWS MSK stack"""

    def __init__(
        self,
        scope: Construct,
        id_: str,
        app_interface_input: AppInterfaceInput,
    ) -> None:
        super().__init__(scope, id_)
        self.data = app_interface_input.data
        self.provision = app_interface_input.provision
        self._init_providers()
        self._run()

    def _init_providers(self) -> None:
        S3Backend(
            self,
            bucket=self.provision.module_provision_data.tf_state_bucket,
            key=self.provision.module_provision_data.tf_state_key,
            encrypt=True,
            region=self.provision.module_provision_data.tf_state_region,
            dynamodb_table=self.provision.module_provision_data.tf_state_dynamodb_table,
            profile="external-resources-state",
        )
        AwsProvider(
            self,
            "Aws",
            region=self.data.region,
            default_tags=self.data.default_tags,
        )
        RandomProvider(self, "Random")

    def _msk_configuration(self) -> MskConfiguration:
        """Create the MSK configuration"""
        msk_version_str = self.data.kafka_version.replace(".", "-")
        msk_config_name = f"{self.data.identifier}-{msk_version_str}"
        return MskConfiguration(
            self,
            msk_config_name,
            name=msk_config_name,
            server_properties=self.data.server_properties,
            kafka_versions=[self.data.kafka_version],
            # lifecycle create_before_destroy is required to ensure that the config is created
            # before it is assigned to the cluster
            lifecycle={
                "create_before_destroy": True,
            },
        )

    def _msk_cluster_client_authentication(
        self,
    ) -> MskClusterClientAuthentication | None:
        # client_authentication
        client_authentication = None
        if self.data.client_authentication and self.data.client_authentication.sasl:
            client_authentication = MskClusterClientAuthentication(
                sasl=MskClusterClientAuthenticationSasl(
                    iam=self.data.client_authentication.sasl.iam,
                    scram=self.data.client_authentication.sasl.scram,
                ),
            )
        return client_authentication

    def _msk_cluster_logging_info(self) -> MskClusterLoggingInfo | None:
        logging_info = None
        if (
            self.data.logging_info
            and self.data.logging_info.broker_logs.cloudwatch_logs
        ):
            cloudwatch_log_group = CloudwatchLogGroup(
                self,
                f"{self.data.identifier}-msk-broker-logs",
                name=f"{self.data.identifier}-msk-broker-logs",
                retention_in_days=self.data.logging_info.broker_logs.cloudwatch_logs.retention_in_days,
                tags=self.data.tags,
            )
            logging_info = MskClusterLoggingInfo(
                broker_logs=MskClusterLoggingInfoBrokerLogs(
                    cloudwatch_logs=MskClusterLoggingInfoBrokerLogsCloudwatchLogs(
                        enabled=self.data.logging_info.broker_logs.cloudwatch_logs.enabled,
                        log_group=cloudwatch_log_group.name,
                    ),
                ),
            )
        return logging_info

    def _msk_cluster_open_monitoring(self) -> MskClusterOpenMonitoring | None:
        open_monitoring = None
        if self.data.open_monitoring:
            open_monitoring = MskClusterOpenMonitoring(
                prometheus=MskClusterOpenMonitoringPrometheus(
                    jmx_exporter=MskClusterOpenMonitoringPrometheusJmxExporter(
                        enabled_in_broker=self.data.open_monitoring.prometheus.jmx_exporter.enabled_in_broker,
                    )
                    if self.data.open_monitoring.prometheus.jmx_exporter
                    else None,
                    node_exporter=MskClusterOpenMonitoringPrometheusNodeExporter(
                        enabled_in_broker=self.data.open_monitoring.prometheus.node_exporter.enabled_in_broker,
                    )
                    if self.data.open_monitoring.prometheus.node_exporter
                    else None,
                ),
            )
        return open_monitoring

    def _msk_cluster_broker_node_group_info(self) -> MskClusterBrokerNodeGroupInfo:
        return MskClusterBrokerNodeGroupInfo(
            client_subnets=self.data.broker_node_group_info.client_subnets,
            instance_type=self.data.broker_node_group_info.instance_type,
            security_groups=self.data.broker_node_group_info.security_groups,
            az_distribution=self.data.broker_node_group_info.az_distribution,
            storage_info=MskClusterBrokerNodeGroupInfoStorageInfo(
                ebs_storage_info=MskClusterBrokerNodeGroupInfoStorageInfoEbsStorageInfo(
                    volume_size=self.data.broker_node_group_info.ebs_volume_size,
                ),
            ),
        )

    def _create_scram_secrets(self, msk_cluster: MskCluster) -> None:
        scram_secrets: list[
            tuple[SecretsmanagerSecret, SecretsmanagerSecretVersion]
        ] = []

        # kms
        kms_key = KmsKey(
            self,
            f"{self.data.identifier}-kms-key",
            description="KMS key for MSK SCRAM credentials",
            tags=self.data.tags,
        )
        KmsAlias(
            self,
            f"{self.data.identifier}-msk-scram",
            name=f"alias/{self.data.identifier}-msk-scram",
            target_key_id=kms_key.key_id,
        )

        assert self.data.scram_users is not None  # mypy
        for user, secret in self.data.scram_users.items():
            secret_identifier = f"AmazonMSK_{self.data.identifier}-{user}"
            secret_resource = SecretsmanagerSecret(
                self,
                f"{secret_identifier}-secret",
                name=secret_identifier,
                tags=self.data.tags,
                kms_key_id=kms_key.key_id,
            )

            version_resource = SecretsmanagerSecretVersion(
                self,
                f"{secret_identifier}-secret-version",
                secret_id=secret_resource.arn,
                secret_string=json.dumps(secret, sort_keys=True),
            )

            SecretsmanagerSecretPolicy(
                self,
                f"{secret_identifier}-secret-policy",
                secret_arn=secret_resource.arn,
                policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "AWSKafkaResourcePolicy",
                            "Effect": "Allow",
                            "Principal": {"Service": "kafka.amazonaws.com"},
                            "Action": "secretsmanager:getSecretValue",
                            "Resource": "${" + secret_resource.arn + "}",
                        },
                    ],
                }),
            )
            scram_secrets.append((secret_resource, version_resource))

        # create ONE scram secret association for each secret created above
        MskScramSecretAssociation(
            self,
            f"{self.data.identifier}-scram-secret-link",
            cluster_arn=msk_cluster.arn,
            secret_arn_list=[s.arn for s, _ in scram_secrets],
            depends_on=[v for _, v in scram_secrets],
        )

    def _create_msk_cluster(
        self,
        broker_node_group_info: MskClusterBrokerNodeGroupInfo,
        client_authentication: MskClusterClientAuthentication | None,
        logging_info: MskClusterLoggingInfo | None,
        open_monitoring: MskClusterOpenMonitoring | None,
        msk_config: MskConfiguration,
    ) -> MskCluster:
        return MskCluster(
            self,
            self.data.identifier,
            broker_node_group_info=broker_node_group_info,
            client_authentication=client_authentication,
            cluster_name=self.data.identifier,
            configuration_info=MskClusterConfigurationInfo(
                arn=msk_config.arn,
                revision=msk_config.latest_revision,
            ),
            kafka_version=self.data.kafka_version,
            number_of_broker_nodes=self.data.number_of_broker_nodes,
            logging_info=logging_info,
            open_monitoring=open_monitoring,
            storage_mode=self.data.storage_mode,
            tags=self.data.tags,
        )

    def _outputs(self, msk_cluster: MskCluster) -> None:
        TerraformOutput(
            self,
            self.data.output_prefix + "__zookeeper_connect_string",
            value=msk_cluster.zookeeper_connect_string,
            sensitive=False,
        )

        TerraformOutput(
            self,
            self.data.output_prefix + "__zookeeper_connect_string_tls",
            value=msk_cluster.zookeeper_connect_string_tls,
            sensitive=False,
        )

        TerraformOutput(
            self,
            self.data.output_prefix + "__bootstrap_brokers",
            value=msk_cluster.bootstrap_brokers,
            sensitive=False,
        )

        TerraformOutput(
            self,
            self.data.output_prefix + "__bootstrap_brokers_tls",
            value=msk_cluster.bootstrap_brokers_tls,
            sensitive=False,
        )

        TerraformOutput(
            self,
            self.data.output_prefix + "__bootstrap_brokers_sasl_iam",
            value=msk_cluster.bootstrap_brokers_sasl_iam,
            sensitive=False,
        )

        TerraformOutput(
            self,
            self.data.output_prefix + "__bootstrap_brokers_sasl_scram",
            value=msk_cluster.bootstrap_brokers_sasl_scram,
            sensitive=False,
        )

    def _run(self) -> None:
        """Run the stack"""
        client_authentication = self._msk_cluster_client_authentication()
        msk_cluster = self._create_msk_cluster(
            broker_node_group_info=self._msk_cluster_broker_node_group_info(),
            client_authentication=client_authentication,
            logging_info=self._msk_cluster_logging_info(),
            open_monitoring=self._msk_cluster_open_monitoring(),
            msk_config=self._msk_configuration(),
        )

        # handle user authentication
        if (
            client_authentication
            and client_authentication.sasl
            and client_authentication.sasl.scram
            and self.data.scram_users
        ):
            self._create_scram_secrets(msk_cluster)

        self._outputs(msk_cluster)
