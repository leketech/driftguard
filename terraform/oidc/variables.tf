variable "role_name" {
  description = "Name of the IAM role to create for GitHub Actions"
  type        = string
  default     = "driftguard-github-actions"
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "s3_bucket" {
  description = "Name of the S3 bucket containing Terraform state"
  type        = string
}

variable "dynamodb_table" {
  description = "Name of the DynamoDB table for state locking"
  type        = string
}

variable "eks_cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}