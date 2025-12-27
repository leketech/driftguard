# DriftGuard OIDC Module for GitHub Actions
# This module creates the necessary IAM resources for GitHub Actions to assume AWS roles via OIDC

module "iam_policy" {
  source = "../modules/iam-policy"

  s3_bucket        = var.s3_bucket
  dynamodb_table   = var.dynamodb_table
  eks_cluster_name = var.eks_cluster_name
  aws_region       = var.aws_region
  account_id       = var.account_id
}

data "tls_certificate" "github_actions" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github_actions.certificates[0].sha1_fingerprint]
}

resource "aws_iam_role" "github_actions" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions" {
  name = "${var.role_name}-policy"
  role = aws_iam_role.github_actions.id

  policy = module.iam_policy.policy_json
}