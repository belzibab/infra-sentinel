variable "project_id" { type = string}
variable "region" { type = string}
variable "cluster_name" { type = string}
variable "network_id" { type = string}
variable "subnet_id" { type = string}
variable "pods_range_name" { type = string}
variable "services_range_name" { type = string}

variable "node_count" {
    type = number
    default = 1
}

variable "machine_type" {
    type = string
    default = "e2-standard-2"
}