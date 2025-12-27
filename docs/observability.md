# DriftGuard Observability Guide

This document describes how to set up monitoring and observability for DriftGuard using Prometheus and Grafana.

## Overview

DriftGuard includes built-in Prometheus metrics for comprehensive monitoring and observability of infrastructure drift detection and remediation activities.

## Metrics Exposed

DriftGuard exposes the following Prometheus metrics:

### Drift Detection Metrics
- `driftguard_scrape_duration_seconds` - Histogram of time taken to fetch and compare state
- `driftguard_drift_total` - Counter of total drift events detected
- `driftguard_drift_by_severity` - Counter of drift events labeled by severity (`critical`, `warning`, `info`, `unknown`)
- `driftguard_drift_by_resource` - Counter of drift events labeled by resource type (`aws_eks`, `k8s_deployment`, etc.)

### Remediation Metrics
- `driftguard_remediation_attempts_total` - Counter of total remediation attempts
- `driftguard_remediation_success_total` - Counter of successful remediation count

## Deployment with Monitoring

### Using Helm

To deploy DriftGuard with monitoring enabled:

```bash
# Install with ServiceMonitor enabled for Prometheus discovery
helm install driftguard ./charts/driftguard \
  --namespace driftguard \
  --create-namespace \
  --set serviceMonitor.enabled=true \
  --set prometheusRule.enabled=true
```

### Prometheus Configuration

If using Prometheus without ServiceMonitor, add the following to your Prometheus configuration:

```yaml
- job_name: 'driftguard'
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
    action: replace
    target_label: __metrics_path__
    regex: (.+)
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
    action: replace
    regex: ([0-9]+)
    replacement: $1
    target_label: __port__
  - source_labels: [__meta_kubernetes_pod_name]
    action: replace
    target_label: job
    replacement: driftguard
```

### Grafana Dashboard

Import the provided dashboard to visualize DriftGuard metrics:

1. Navigate to Grafana
2. Go to Dashboards > Manage
3. Click "Import"
4. Upload the dashboard JSON from `charts/driftguard/templates/dashboard-configmap.yaml` or use the raw JSON

## Alerting Rules

The following alerting rules are included:

- `HighCriticalDriftRate` - Alerts when critical drift events exceed the threshold
- `DriftGuardDown` - Alerts when DriftGuard is not responding
- `HighRemediationFailureRate` - Alerts when remediation failure rate is too high

## Example Queries

Here are some useful Prometheus queries for monitoring DriftGuard:

### Drift Events
```
# Rate of drift events by severity over the last 5 minutes
rate(driftguard_drift_by_severity[5m])

# Total drift events in the last hour
increase(driftguard_drift_total[1h])
```

### Remediation Performance
```
# Remediation success rate
rate(driftguard_remediation_success_total[10m]) / rate(driftguard_remediation_attempts_total[10m])

# Remediation failure rate
rate(driftguard_remediation_attempts_total[10m]) - rate(driftguard_remediation_success_total[10m])
```

### Performance
```
# 95th percentile of scrape duration
histogram_quantile(0.95, rate(driftguard_scrape_duration_seconds_bucket[5m]))
```

## Troubleshooting

### Metrics Not Appearing

1. Verify that the DriftGuard pods are running and healthy
2. Check that the Prometheus annotations are correctly applied:
   ```bash
   kubectl describe pod -n driftguard -l app=driftguard
   ```
3. Ensure Prometheus is configured to scrape pods with the `prometheus.io/scrape` annotation

### Dashboard Not Loading

1. Verify that the dashboard ConfigMap was created:
   ```bash
   kubectl get configmap -n driftguard
   ```
2. Check Grafana's dashboard discovery settings

## Architecture

The observability stack follows this architecture:

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│  DriftGuard     │───▶│  Prometheus  │───▶│   Grafana   │
│  Agent          │    │              │    │             │
│                 │    │              │    │             │
│ • Exposes /metrics │ │ • Discovers  │    │ • Visualizes│
│ • Custom metrics   │ │   metrics    │    │   metrics   │
│ • Health checks    │ │ • Stores     │    │ • Dashboards│
└─────────────────┘    │   data       │    │ • Alerts    │
                       └──────────────┘    └─────────────┘
```

This architecture provides:
- Real-time metrics collection
- Historical data storage
- Visual dashboards
- Alerting capabilities
```
