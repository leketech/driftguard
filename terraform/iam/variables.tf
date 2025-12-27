variable "role_name" {
  description = "Name of the IAM role to create"
  type        = string
  default     = "driftguard-agent"
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