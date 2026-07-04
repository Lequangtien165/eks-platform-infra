# Kiểm tra và xác nhận Terraform chạy đúng account, region, naming convertion

output "aws_account_id" {
  description = "AWS account ID used by this environment."
  value       = data.aws_caller_identity.current.account_id
}

output "aws_caller_arn" {
  description = "Caller ARN used by Terraform"
  value       = data.aws_caller_identity.current.arn
}

output "aws_region" {
  description = "AWS region used by this environment."
  value       = data.aws_region.current.name
}

output "name_prefix" {
  description = "Common naming prefix for this environment."
  value       = local.name_prefix
}

# Khai báo output cho VPC
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

# Khai báo output cho EKS
output "cluster_name" {
    value = module.eks.cluster_name
}

output "cluster_endpoint" {
    value = module.eks.cluster_endpoint
}

output "cluster_version" {
    value = module.eks.cluster_version
}
