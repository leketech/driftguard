# DriftGuard Architecture

## Overview

DriftGuard follows a modular architecture designed for autonomous infrastructure drift detection and remediation. The system consists of several key components that work together to monitor, analyze, and reconcile infrastructure state.

## Components

### 1. Detectors
Detectors are responsible for collecting state information from various sources:

- **AWS Detector**: Collects desired state from Terraform and live state from AWS APIs
- **Kubernetes Detector**: Collects desired state from Helm templates and live state from Kubernetes API

### 2. Diff Analyzer
The diff analyzer computes structured differences between desired and live states, identifying any configuration drift.

### 3. Policy Engine
The policy engine evaluates drift reports against configurable policies to classify severity and determine appropriate actions.

### 4. Reporter
The reporter generates and stores reports in various formats (JSON, S3, file system) and can integrate with notification systems.

### 5. Configuration Manager
Manages configuration loading from YAML files and environment variables.

## Data Flow

1. **State Collection**: Detectors collect desired state from IaC (Terraform/Helm) and live state from cloud providers (AWS/Kubernetes)
2. **Diff Computation**: Diff analyzer computes structured differences between desired and live states
3. **Policy Evaluation**: Policy engine evaluates drift reports against configured policies
4. **Action Determination**: Based on policy evaluation, appropriate actions are determined (remediate, alert, ignore)
5. **Reporting**: Results are reported through various channels (logs, S3, GitHub PRs)

## Deployment Options

DriftGuard can be deployed in multiple ways:

1. **Kubernetes CronJob**: Scheduled execution for periodic drift detection
2. **Kubernetes Deployment**: Continuous monitoring deployment
3. **CLI Tool**: Manual execution for ad-hoc drift detection

Each deployment method is available via:
- **Kubernetes Manifests**: Direct application of YAML files from the `manifests/` directory
- **Helm Chart**: Using the Helm chart from `charts/driftguard/` with configuration options

## Security Model

DriftGuard follows the principle of least privilege:

- **IAM Roles**: Scoped to read-only access for AWS resources with minimal required permissions
- **Kubernetes RBAC**: ServiceAccount with get/list permissions only
- **Secrets Management**: Git credentials via Kubernetes Secrets, never hard-coded
- **Network Isolation**: Runs in isolated namespace with optional NetworkPolicy restrictions
- **OIDC Authentication**: Secure authentication for CI/CD pipelines using OpenID Connect

Auto-remediation is disabled by default and must be explicitly enabled per environment.

## Observability

DriftGuard includes built-in Prometheus metrics for monitoring and observability:

- **Metrics Collection**: Custom Prometheus metrics track drift events, remediation success rates, and agent performance
- **Service Discovery**: Prometheus annotations enable automatic service discovery
- **Alerting**: Pre-configured alerting rules for critical drift events and agent health
- **Visualization**: Grafana dashboards for visualizing drift trends and remediation effectiveness