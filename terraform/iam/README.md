# DriftGuard IAM Module

This module creates the necessary IAM resources for DriftGuard to operate. It uses the shared IAM policy module to ensure consistent permissions across all DriftGuard components.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | >= 4.0 |

## Providers

| Name | Version |
|------|---------|
| aws | >= 4.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| role\_name | Name of the IAM role to create | `string` | `"driftguard-agent"` | no |
| s3\_bucket | Name of the S3 bucket containing Terraform state | `string` | n/a | yes |
| dynamodb\_table | Name of the DynamoDB table for state locking | `string` | n/a | yes |
| eks\_cluster\_name | Name of the EKS cluster | `string` | n/a | yes |
| aws\_region | AWS region | `string` | n/a | yes |
| account\_id | AWS account ID | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| role\_arn | ARN of the created IAM role |
| role\_name | Name of the created IAM role |

## Module Structure

This module consumes the shared `iam-policy` module to ensure consistent permissions across all DriftGuard components.