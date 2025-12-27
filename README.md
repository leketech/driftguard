# DriftGuard

Autonomous Infrastructure Drift Detector & Self-Healer for DevOps Engineers

## 📚 Table of Contents
- [Overview](#overview)
- [Why DriftGuard?](#why-driftguard)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Security Model](#security-model)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Usage Examples](#usage-examples)
- [Policies & Remediation Rules](#policies--remediation-rules)
- [Extending DriftGuard](#extending-driftguard)
- [Roadmap](#roadmap)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

DriftGuard is an autonomous AI-assisted DevOps agent that continuously compares your infrastructure-as-code (IaC) state (Terraform + Helm) with live cloud and Kubernetes resources. It detects configuration drift, classifies its risk level, and either auto-remediates or opens a pull request for human review—helping maintain system integrity, security, and compliance.

Built for engineers managing AWS EKS, Terraform, and GitOps workflows, DriftGuard runs natively in Kubernetes and integrates with your existing CI/CD and monitoring stack.

## Why DriftGuard?

Infrastructure drift—unauthorized or accidental changes to live systems—leads to:

- Security gaps (e.g., open security groups)
- Operational surprises during incident response
- Failed Terraform applies due to state conflicts
- Compliance violations

Traditional tools (e.g., terraform plan) only detect drift on-demand. DriftGuard proactively monitors, intelligently triages, and safely reconciles—turning drift management into a self-healing capability.

## Key Features

✅ **Multi-layer drift detection**
- AWS resources (via Terraform state)
- Kubernetes workloads (via Helm release manifests)

✅ **Risk-aware classification**
- Uses rule-based + lightweight LLM heuristics to label drift as safe, warning, or critical

✅ **Policy-driven remediation**
- Auto-fix in dev environments
- GitHub PR + Slack alert for production

✅ **Git-native workflow**
- All actions are logged as Git commits or PR comments

✅ **Runs inside your cluster**
- Deploy as a Kubernetes CronJob or Deployment

✅ **Audit-ready**
- Immutable JSON reports stored in S3 or Git

✅ **Observability-first**
- Built-in Prometheus metrics for drift events, remediation success rates, and agent performance
- Pre-configured Grafana dashboards for visualizing drift trends
- Alerting rules for critical drift events and agent health

## Architecture

See [Architecture Documentation](docs/architecture.md) for detailed information.

## Observability & Monitoring

DriftGuard includes built-in Prometheus metrics and Grafana dashboards for comprehensive observability:

### Metrics Exposed
- `driftguard_scrape_duration_seconds` - Time taken to fetch and compare state
- `driftguard_drift_total` - Total drift events detected
- `driftguard_drift_by_severity` - Drift events labeled by severity (critical, warning, info)
- `driftguard_drift_by_resource` - Drift events labeled by resource type (aws_eks, k8s_deployment, etc.)
- `driftguard_remediation_attempts_total` - Total remediation attempts
- `driftguard_remediation_success_total` - Successful remediation count

### Deployment with Monitoring

When deploying with Helm, enable monitoring features:

```bash
# Enable ServiceMonitor for automatic Prometheus discovery
helm install driftguard ./charts/driftguard \
  --namespace driftguard \
  --set serviceMonitor.enabled=true \
  --set prometheusRule.enabled=true
```

### Grafana Dashboard

A pre-built Grafana dashboard is included to visualize drift trends, remediation success rates, and agent performance.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.11+ (with pydantic, boto3, kubernetes) |
| Container | Alpine-based Docker image |
| Orchestration | Kubernetes CronJob / Argo Workflows |
| IaC Tools | Terraform CLI, Helm CLI |
| Cloud | AWS (EKS, S3, DynamoDB, IAM) |
| Git | GitHub API (for PRs/comments) |
| AI Component | Rule engine + optional TinyLLM for log analysis |
| Logging | Structured JSON → S3 / stdout / GitHub |

## Security Model

DriftGuard follows the principle of least privilege:

- **IAM Role**: Scoped to read-only access for AWS resources with minimal required permissions
- **Kubernetes RBAC**: ServiceAccount with get/list permissions only
- **Secrets Management**: Git credentials via Kubernetes Secrets, never hard-coded
- **Network Isolation**: Runs in isolated namespace with optional NetworkPolicy restrictions
- **OIDC Authentication**: Secure authentication for CI/CD pipelines using OpenID Connect

🔒 Auto-remediation is disabled by default. You must explicitly allow it per environment.

## Getting Started

See [Getting Started Guide](docs/getting-started.md) for detailed instructions.

### Prerequisites

- Kubernetes cluster (tested on EKS 1.30+)
- Terraform state stored in S3 with DynamoDB locking
- Helm releases managed via Git (no kubectl apply mix)
- GitHub Personal Access Token (for PR automation)

### Quick Start

```bash
git clone https://github.com/leketech/driftguard.git
cd driftguard

# Set environment variables
export GIT_REPO_URL="https://github.com/leketech/driftguard.git"
export GIT_BRANCH="main"
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="909807568796"
export TERRAFORM_STATE_KEY="terraform/state.tfstate"
export GITHUB_TOKEN="your-github-token"

# Deploy via Kubernetes manifests
kubectl create namespace driftguard
kubectl apply -f manifests/rbac.yaml
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/cronjob.yaml
```

## Configuration

All settings are managed via `config/policies.yaml` and Kubernetes ConfigMap.

See [Getting Started Guide](docs/getting-started.md#configuration) for detailed configuration options.

## Deployment

### 1. Create IAM Role (via Terraform)

Use the provided terraform/iam module:

```hcl
module "driftguard_iam" {
  source = "./terraform/iam"
  role_name = "driftguard-agent"
  s3_bucket = "your-terraform-state-bucket"
  dynamodb_table = "terraform-locks"
  eks_cluster_name = "your-eks-cluster"
}
```

### 2. Configure OIDC for GitHub Actions (Recommended)

For secure authentication in CI/CD pipelines, use the OIDC module:

```hcl
module "driftguard_oidc" {
  source = "./terraform/oidc"
  role_name = "driftguard-github-actions"
  github_org = "your-github-org"
  github_repo = "https://github.com/leketech/driftguard.git"
  s3_bucket = "driftguard-bucket"
  dynamodb_table = "drift-locks"
  eks_cluster_name = "driftguard-cluster"
  aws_region = "us-east-1"
  account_id = "909807568796"
}
```

### 3. Apply Kubernetes Manifests

```bash
kubectl create namespace driftguard
kubectl apply -f manifests/rbac.yaml
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/cronjob.yaml  # or deployment.yaml
```

### 4. Deploy via Helm

**Option A: Scheduled execution (CronJob)**

```bash
helm install driftguard ./charts/driftguard \
  --namespace driftguard \
  --set git.repoUrl="https://github.com/leketech/driftguard.git" \
  --set aws.region="us-east-1" \
  --set aws.accountId="909807568796"
```

**Option B: Continuous monitoring (Deployment)**

```bash
helm install driftguard ./charts/driftguard \
  --namespace driftguard \
  --set schedule="" \
  --set git.repoUrl="https://github.com/your-org/your-iac-repo.git" \
  --set aws.region="us-east-1" \
  --set aws.accountId="909807568796"
```

### 5. GitHub Actions CI/CD

The project includes a GitHub Actions workflow in `.github/workflows/ci-cd.yml` that:
- Runs tests on pull requests
- Builds and pushes Docker images
- Deploys to Kubernetes using OIDC authentication

To use it, configure the required secrets in your GitHub repository:
- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` for container registry
- `AWS_ACCOUNT_ID` and `AWS_REGION` for OIDC authentication

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

## Policies & Remediation Rules

DriftGuard uses a two-tier policy system:

1. **Environment Policy**: Define which namespaces/clusters allow auto-remediation.
2. **Resource Sensitivity Rules**:
   - `critical`: Always require approval (e.g., IAM roles, network ACLs)
   - `warning`: Auto-remediate in dev, alert in prod
   - `ignored`: Never report (e.g., timestamps, provider-generated fields)

You can extend rules using Python plugins (`agent/rules/custom.py`).

## Extending DriftGuard

### Add a New Detector

1. Create `agent/detectors/custom_drift.py`
2. Implement `detect()` method returning `DriftReport`
3. Register in `main.py`

### Add AI Triage (Advanced)

1. Enable `USE_LLM=true`
2. Mount a quantized TinyLLM (e.g., TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF)
3. Use for summarizing drift impact from past incident logs

### Support New Cloud Provider

Implement `CloudDetector` interface for GCP/Azure

## Roadmap

- ✅ MVP (v0.1): AWS + K8s drift detection, GitHub alerts
- 🔜 v0.2: Auto-remediation with dry-run mode
- 🔜 v0.3: UI dashboard (Grafana plugin)
- 🔜 v1.0: Multi-cloud, webhook integrations, drift forecasting

## Testing

DriftGuard includes unit tests to ensure code quality and reliability. See the [tests/README.md](tests/README.md) for details on how to run tests.

## Contributing

We welcome PRs! Please:

1. Fork the repo
2. Create a feature branch
3. Write tests (`tests/`)
4. Update docs
5. Submit PR to main

## License

Apache License 2.0 — free to use, modify, and distribute, even commercially.