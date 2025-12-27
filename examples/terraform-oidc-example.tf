# Example Terraform configuration for DriftGuard OIDC role
# This example shows how to use the OIDC module which consumes the shared IAM policy module

module "driftguard_oidc" {
  source = "../terraform/oidc"

  role_name        = "driftguard-github-actions"
  github_org       = "your-github-org"
  github_repo      = "driftguard"
  s3_bucket        = "your-terraform-state-bucket"
  dynamodb_table   = "terraform-locks"
  eks_cluster_name = "your-eks-cluster"
  aws_region       = "us-east-1"
  account_id       = "909807568796"
}

output "driftguard_oidc_role_arn" {
  value = module.driftguard_oidc.role_arn
}

output "driftguard_oidc_provider_arn" {
  value = module.driftguard_oidc.openid_connect_provider_arn
}