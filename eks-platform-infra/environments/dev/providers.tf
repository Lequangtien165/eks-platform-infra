# Chốt version cho Terraform, tránh lệch môi trường

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Nói Terraform biết sẽ dùng AWS ở đâu và bằng credentials nào

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  # Giúp AWS resource đều có tag thống nhất
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}