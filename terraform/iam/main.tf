# DriftGuard IAM Module
# This module creates the necessary IAM resources for DriftGuard to operate

module "iam_policy" {
  source = "../modules/iam-policy"

  s3_bucket        = var.s3_bucket
  dynamodb_table   = var.dynamodb_table
  eks_cluster_name = var.eks_cluster_name
  aws_region       = var.aws_region
  account_id       = var.account_id
}

resource "aws_iam_role" "driftguard" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "driftguard" {
  name = "${var.role_name}-policy"
  role = aws_iam_role.driftguard.id

  policy = module.iam_policy.policy_json
}