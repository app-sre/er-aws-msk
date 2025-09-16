variable "broker_node_group_info" {
  type = object({ client_subnets = list(string), instance_type = string, security_groups = list(string), az_distribution = string, ebs_volume_size = number })
}

variable "client_authentication" {
  type    = object({ sasl = object({ iam = bool, scram = bool }) })
  default = null
}

variable "identifier" {
  type = string
}

variable "kafka_version" {
  type = string
}

variable "logging_info" {
  type    = object({ broker_logs = object({ cloudwatch_logs = object({ enabled = bool, retention_in_days = number }) }) })
  default = null
}

variable "number_of_broker_nodes" {
  type = number
}

variable "open_monitoring" {
  type    = object({ prometheus = object({ jmx_exporter = object({ enabled_in_broker = bool }), node_exporter = object({ enabled_in_broker = bool }) }) })
  default = null
}

variable "output_prefix" {
  type = string
}

variable "output_resource_name" {
  type    = string
  default = null
}

variable "region" {
  type = string
}

variable "scram_users" {
  type    = map(map(string))
  default = null
}

variable "server_properties" {
  type = string
}

variable "storage_mode" {
  type    = string
  default = null
}

variable "tags" {
  type    = map(string)
  default = {}
}
