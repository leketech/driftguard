# Getting Started with DriftGuard

## Prerequisites

Before deploying DriftGuard, ensure you have:

1. **Kubernetes cluster** (tested on EKS 1.30+)
2. **Terraform state** stored in S3 with DynamoDB locking
3. **Helm releases** managed via Git (no kubectl apply mix)
4. **GitHub Personal Access Token** (for PR automation)
5. **AWS Account** with permissions to create IAM roles and OIDC providers (for CI/CD authentication)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/leketech/driftguard.git
cd driftguard
```

### 2. Configure DriftGuard

Edit `config/policies.yaml` to define your remediation policies and drift rules:

```yaml
remediation:
  auto_apply:
    - environment: dev
      namespaces: ["default", "staging"]
      resources:
        - "*"
    - environment: prod
      namespaces: []
      resources: []  # ← requires manual approval
drift_rules:
  ignore:
    - aws_instance.tags.Terraform
    - k8s_pod.status.hostIP
  critical:
    - aws_security_group.ingress
    - k8s_deployment.spec.template.spec.containers.image
```

### 3. Set Environment Variables

```bash
export GIT_REPO_URL="https://github.com/your-org/your-iac-repo.git"
export GIT_BRANCH="main"
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="909807568796"
export TERRAFORM_STATE_KEY="terraform/state.tfstate"
export GITHUB_TOKEN="your-github-token"
```

### 4. Deploy via Kubernetes Manifests

```bash
kubectl create namespace driftguard
kubectl apply -f manifests/rbac.yaml
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/deployment.yaml  # or cronjob.yaml
```

### 5. Deploy via Helm (Alternative)

```bash
helm install driftguard ./charts/driftguard \
  --namespace driftguard \
  --set git.repoUrl="https://github.com/your-org/your-iac-repo.git" \
  --set aws.region="us-east-1"
```

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| GIT_REPO_URL | IaC Git repository | https://github.com/your-org/your-iac-repo.git |
| GIT_BRANCH | Branch to monitor | main |
| AWS_REGION | Target AWS region | us-east-1 |
| AWS_ACCOUNT_ID | AWS account ID | 909807568796 |
| TERRAFORM_STATE_KEY | S3 key for .tfstate | terraform/state.tfstate |
| GITHUB_TOKEN | For PR automation | ghp_xxx |

### Policies

Configure policies in `config/policies.yaml`:

- **remediation.auto_apply**: Define which environments/namespaces allow auto-remediation
- **drift_rules.ignore**: Patterns to ignore during drift detection
- **drift_rules.critical**: Patterns to classify as critical drift

### OIDC Authentication for CI/CD

For secure authentication in CI/CD pipelines, DriftGuard supports OpenID Connect (OIDC) authentication with AWS. This eliminates the need to store long-lived AWS credentials as GitHub secrets.

To configure OIDC:

1. Deploy the OIDC Terraform module:

```hcl
module "driftguard_oidc" {
  source = "../terraform/oidc"
  role_name = "driftguard-github-actions"
  github_org = "your-github-org"
  github_repo = "driftguard"
  s3_bucket = "your-terraform-state-bucket"
  dynamodb_table = "terraform-locks"
  eks_cluster_name = "your-eks-cluster"
  aws_region = "us-east-1"
  account_id = "909807568796"
}
```

2. The GitHub Actions workflow will automatically use the OIDC role for authentication with AWS.

Both the IAM and OIDC modules now use a shared IAM policy module to ensure consistent permissions across all DriftGuard components. This modular approach makes the Terraform code more maintainable and reusable.

## Usage Examples

### Example 1: Detect EKS Node Group Size Drift

**Desired**: node_count = 3 in Terraform
**Live**: Someone manually scaled to 5 via AWS Console
**DriftGuard Action**:
- Logs drift as Warning
- Opens PR: "Revert EKS node group to 3 instances"
- Slack alert sent to #infra-alerts

### Example 2: Auto-fix Dev Namespace Image Tag

**Desired**: image: myapp:v1.2 in Helm chart (dev branch)
**Live**: Pod running v1.1 (stale deploy)
**DriftGuard Action**:
- Classifies as Safe (non-prod)
- Runs helm upgrade --namespace dev automatically
- Commits reconciliation log to S3