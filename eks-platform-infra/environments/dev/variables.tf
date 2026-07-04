# Khai báo các biến đầu vào mà môi trường dev cần, tách phần khai báo biến khỏi phần gán giá trị

variable "project_name" {
  description = "Project name used for naming and tagging resources."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "aws_region" {
  description = "AWS region for this environment."
  type        = string
}

variable "aws_profile" {
  description = "AWS CLI profile used by Terraform."
  type        = string
}

# Khai báo biến cho VPC
variable "vpc_cidr" {
  type = string
}

variable "azs" {
  type = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_subnet_cidrs" {
  type = list(string)
}

variable "cluster_name" {
  type = string
}

# Khai báo biến cho EKS
variable "cluster_version" {
  type = string
}

variable "node_group_name" {
  type = string
}

variable "desired_size" {
  type = number
}

variable "min_size" {
  type = number
}

variable "max_size" {
  type = number
}

variable "instance_types" {
  type = list(string)
}

