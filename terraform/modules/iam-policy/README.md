# DriftGuard IAM Policy Module

This module creates a reusable IAM policy for DriftGuard operations. It defines the minimum required permissions for DriftGuard to operate with AWS resources.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | >= 4.0 |

## Providers

No providers.

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| s3\_bucket | Name of the S3 bucket containing Terraform state | `string` | n/a | yes |
| dynamodb\_table | Name of the DynamoDB table for state locking | `string` | n/a | yes |
| eks\_cluster\_name | Name of the EKS cluster | `string` | n/a | yes |
| aws\_region | AWS region | `string` | n/a | yes |
| account\_id | AWS account ID | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| policy\_json | JSON representation of the IAM policy |