
provider "aws" {
  region = var.region
  default_tags {
    tags = var.tags
  }
}


resource "aws_kms_key" "this" {
  description = "KMS key for MSK SCRAM credentials"
  tags        = var.tags
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.identifier}-msk-scram"
  target_key_id = aws_kms_key.this.key_id
}

resource "aws_cloudwatch_log_group" "this" {
  count = var.logging_info != null ? 1 : 0

  name              = "${var.identifier}-msk-broker-logs"
  retention_in_days = var.logging_info.broker_logs.cloudwatch_logs.retention_in_days
  tags              = var.tags
}

resource "aws_msk_configuration" "this" {
  name              = "${var.identifier}-${replace(var.kafka_version, ".", "-")}"
  kafka_versions    = [var.kafka_version]
  server_properties = var.server_properties

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_secretsmanager_secret" "this" {
  for_each   = var.scram_users
  name       = "AmazonMSK_${var.identifier}-${each.key}"
  tags       = var.tags
  kms_key_id = aws_kms_key.this.key_id
}

resource "aws_secretsmanager_secret_version" "this" {
  for_each      = var.scram_users
  secret_id     = aws_secretsmanager_secret.this[each.key].id
  secret_string = jsonencode(each.value)
}

resource "aws_secretsmanager_secret_policy" "this" {
  for_each   = var.scram_users
  secret_arn = aws_secretsmanager_secret.this[each.key].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSKafkaResourcePolicy"
        Effect = "Allow"
        Principal = {
          Service = "kafka.amazonaws.com"
        }
        Action   = "secretsmanager:getSecretValue"
        Resource = aws_secretsmanager_secret.this[each.key].arn
      }
    ]
  })
}

resource "aws_msk_scram_secret_association" "this" {
  count = length(var.scram_users) > 0 && try(var.client_authentication.sasl.scram, false) ? 1 : 0

  cluster_arn     = aws_msk_cluster.this.arn
  secret_arn_list = [for secret in aws_secretsmanager_secret.this : secret.arn]

  depends_on = [
    aws_secretsmanager_secret_version.this
  ]
}

resource "aws_msk_cluster" "this" {
  cluster_name           = var.identifier
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.number_of_broker_nodes
  storage_mode           = var.storage_mode
  tags                   = var.tags

  configuration_info {
    arn      = aws_msk_configuration.this.arn
    revision = aws_msk_configuration.this.latest_revision
  }

  dynamic "client_authentication" {
    for_each = var.client_authentication != null ? [1] : []
    content {
      sasl {
        iam   = var.client_authentication.sasl.iam
        scram = var.client_authentication.sasl.scram
      }
    }
  }

  dynamic "logging_info" {
    for_each = var.logging_info != null ? [1] : []
    content {
      broker_logs {
        cloudwatch_logs {
          enabled   = var.logging_info.broker_logs.cloudwatch_logs.enabled
          log_group = aws_cloudwatch_log_group.this[0].name
        }
      }
    }
  }

  dynamic "open_monitoring" {
    for_each = var.open_monitoring != null ? [1] : []
    content {
      prometheus {
        jmx_exporter {
          enabled_in_broker = var.open_monitoring.prometheus.jmx_exporter.enabled_in_broker
        }
        node_exporter {
          enabled_in_broker = var.open_monitoring.prometheus.node_exporter.enabled_in_broker
        }
      }
    }
  }

  broker_node_group_info {
    client_subnets  = var.broker_node_group_info.client_subnets
    instance_type   = var.broker_node_group_info.instance_type
    security_groups = var.broker_node_group_info.security_groups
    az_distribution = var.broker_node_group_info.az_distribution
    storage_info {
      ebs_storage_info {
        volume_size = var.broker_node_group_info.ebs_volume_size
      }
    }
  }
}
