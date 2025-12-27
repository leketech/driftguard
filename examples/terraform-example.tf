# Example Terraform configuration for DriftGuard IAM role
# This example shows how to use the IAM module which consumes the shared IAM policy module

module "driftguard_iam" {
  source = "../terraform/iam"

  role_name        = "driftguard-agent"
  s3_bucket        = "your-terraform-state-bucket"
  dynamodb_table   = "terraform-locks"
  eks_cluster_name = "your-eks-cluster"
  aws_region       = "us-east-1"
  account_id       = "909807568796"
}

output "driftguard_role_arn" {
  value = module.driftguard_iam.role_arn
}