# Đọc account info, region từ provider, tạo biến nội bộ để tái sử dụng

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# Thêm module VPC
module "vpc" {
  source = "../../modules/vpc"

  name_prefix          = local.name_prefix
  cluster_name         = var.cluster_name
  vpc_cidr             = var.vpc_cidr
  azs                  = var.azs
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# Thêm module EKS
module "eks" {
    source = "../../modules/eks"

    cluster_name = var.cluster_name
    cluster_version = var.cluster_version
    subnet_ids = module.vpc.private_subnet_ids

    node_group_name = var.node_group_name
    desired_size = var.desired_size
    min_size = var.min_size
    max_size = var.max_size
    instance_types = var.instance_types
}

