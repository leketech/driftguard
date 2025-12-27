# Complete example showing how to use both DriftGuard IAM modules

# Module for the DriftGuard agent IAM role
module "driftguard_agent_iam" {
  source = "../terraform/iam"

  role_name        = "driftguard-agent"
  s3_bucket        = "my-terraform-state-bucket"
  dynamodb_table   = "terraform-locks"
  eks_cluster_name = "my-eks-cluster"
  aws_region       = "us-west-2"
  account_id       = "909807568796"
}

# Module for the GitHub Actions OIDC role
module "driftguard_github_actions_oidc" {
  source = "../terraform/oidc"

  role_name        = "driftguard-github-actions"
  github_org       = "my-org"
  github_repo      = "driftguard"
  s3_bucket        = "my-terraform-state-bucket"
  dynamodb_table   = "terraform-locks"
  eks_cluster_name = "my-eks-cluster"
  aws_region       = "us-west-2"
  account_id       = "909807568796"
}

# Outputs
output "driftguard_agent_role_arn" {
  value = module.driftguard_agent_iam.role_arn
}

output "driftguard_github_actions_role_arn" {
  value = module.driftguard_github_actions_oidc.role_arn
}

output "driftguard_github_actions_provider_arn" {
  value = module.driftguard_github_actions_oidc.openid_connect_provider_arn
}