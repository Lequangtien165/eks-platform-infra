# Khai báo nơi Terraform lưu state

terraform {
  backend "s3" {
    bucket  = "nhf-eks-platform-tfstate-123456"
    key     = "dev/terraform.tfstate"
    region  = "ap-southeast-1"
    profile = "nhf-project"
    encrypt = true
    # dynamodb_table = "nhf-eks-platform-tf-lock"
  }
}