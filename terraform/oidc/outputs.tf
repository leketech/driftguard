output "role_arn" {
  description = "ARN of the created IAM role for GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}

output "role_name" {
  description = "Name of the created IAM role for GitHub Actions"
  value       = aws_iam_role.github_actions.name
}

output "openid_connect_provider_arn" {
  description = "ARN of the created OpenID Connect provider"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}