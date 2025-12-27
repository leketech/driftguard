#!/usr/bin/env python3
"""
DriftGuard Main Entry Point
Autonomous Infrastructure Drift Detector & Self-Healer for DevOps Engineers
"""

import os
import sys
import logging
from typing import Dict, Any
import threading
from prometheus_client import start_http_server, Counter, Histogram, Gauge

from config_loader import load_config
from detectors.aws_detector import AWSDetector
from detectors.k8s_detector import K8sDetector
from detectors.kafka_detector import KafkaDetector
from diff_analyzer import DiffAnalyzer
from policy_engine import PolicyEngine
from reporter import Reporter

# Prometheus metrics
DRIFT_TOTAL = Counter('driftguard_drift_total', 'Total drift events detected')
DRIFT_BY_SEVERITY = Counter('driftguard_drift_by_severity', 'Drift by severity', ['severity'])
DRIFT_BY_RESOURCE = Counter('driftguard_drift_by_resource', 'Drift by resource type', ['resource_type'])
REMEDIATION_ATTEMPTS = Counter('driftguard_remediation_attempts_total', 'Remediation attempts')
REMEDIATION_SUCCESS = Counter('driftguard_remediation_success_total', 'Successful remediations')
SCRAPE_DURATION = Histogram('driftguard_scrape_duration_seconds', 'Scrape and compare duration')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Start metrics server in a separate thread
def start_metrics_server():
    start_http_server(8000)

metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
metrics_thread.start()

def main():
    """Main entry point for DriftGuard"""
    logger.info("Starting DriftGuard...")
    
    # Load configuration
    config = load_config()
    
    # Initialize detectors
    aws_detector = AWSDetector(config)
    k8s_detector = K8sDetector(config)
    
    # Check if Kafka is configured and enabled before initializing
    kafka_config = config.get('kafka', {})
    kafka_bootstrap_servers = kafka_config.get('bootstrap_servers', '')
    
    if kafka_bootstrap_servers:
        try:
            kafka_detector = KafkaDetector(config)
            logger.info("Kafka detector initialized successfully")
            kafka_enabled = True
        except Exception as e:
            logger.warning(f"Failed to initialize Kafka detector: {e}. Continuing without Kafka.")
            kafka_enabled = False
    else:
        logger.info("Kafka not configured, disabling Kafka functionality")
        kafka_enabled = False
    
    # Initialize other components
    diff_analyzer = DiffAnalyzer()
    policy_engine = PolicyEngine(config)
    reporter = Reporter(config)
    
    # Collect desired state from IaC
    logger.info("Collecting desired state from IaC...")
    desired_aws_state = aws_detector.get_desired_state()
    desired_k8s_state = k8s_detector.get_desired_state()
    
    if kafka_enabled:
        desired_kafka_state = kafka_detector.get_desired_state()
    else:
        desired_kafka_state = {"topics": [], "acls": [], "brokers": [], "quotas": []}
    
    # Collect live state from cloud and k8s
    logger.info("Collecting live state from cloud and k8s...")
    live_aws_state = aws_detector.get_live_state()
    live_k8s_state = k8s_detector.get_live_state()
    
    if kafka_enabled:
        live_kafka_state = kafka_detector.get_live_state()
    else:
        live_kafka_state = {"topics": [], "brokers": [], "acls": [], "quotas": []}
    
    # Compute diffs
    logger.info("Computing differences...")
    with SCRAPE_DURATION.time():
        aws_diffs = diff_analyzer.compute_diffs(desired_aws_state, live_aws_state)
        k8s_diffs = diff_analyzer.compute_diffs(desired_k8s_state, live_k8s_state)
        if kafka_enabled:
            kafka_diffs = diff_analyzer.compute_diffs(desired_kafka_state, live_kafka_state)
        else:
            kafka_diffs = []
        
        # Count drift events
        for diff in aws_diffs:
            DRIFT_TOTAL.inc()
            severity = getattr(diff, 'severity', 'unknown')
            if hasattr(severity, 'value'):
                severity = severity.value
            resource_type = getattr(diff, 'resource_type', 'unknown')
            DRIFT_BY_SEVERITY.labels(severity=severity).inc()
            DRIFT_BY_RESOURCE.labels(resource_type=resource_type).inc()
        
        for diff in k8s_diffs:
            DRIFT_TOTAL.inc()
            severity = getattr(diff, 'severity', 'unknown')
            if hasattr(severity, 'value'):
                severity = severity.value
            resource_type = getattr(diff, 'resource_type', 'unknown')
            DRIFT_BY_SEVERITY.labels(severity=severity).inc()
            DRIFT_BY_RESOURCE.labels(resource_type=resource_type).inc()
        
        if kafka_enabled:
            for diff in kafka_diffs:
                DRIFT_TOTAL.inc()
                severity = getattr(diff, 'severity', 'unknown')
                if hasattr(severity, 'value'):
                    severity = severity.value
                resource_type = getattr(diff, 'resource_type', 'unknown')
                DRIFT_BY_SEVERITY.labels(severity=severity).inc()
                DRIFT_BY_RESOURCE.labels(resource_type=resource_type).inc()
    
    # Apply policies
    logger.info("Applying policies...")
    aws_actions = policy_engine.evaluate(aws_diffs)
    k8s_actions = policy_engine.evaluate(k8s_diffs)
    if kafka_enabled:
        kafka_actions = policy_engine.evaluate(kafka_diffs)
    else:
        kafka_actions = []
    
    # Count remediation attempts and successes
    all_actions = aws_actions + k8s_actions
    if kafka_enabled:
        all_actions += kafka_actions
    for action in all_actions:
        if hasattr(action, 'action_type') and action.action_type in ['remediate', 'alert']:
            REMEDIATION_ATTEMPTS.inc()
            if hasattr(action, 'status') and action.status == 'success':
                REMEDIATION_SUCCESS.inc()
    
    # Combine all diffs and actions into a single report
    logger.info("Reporting results...")
    all_diffs = aws_diffs + k8s_diffs
    if kafka_enabled:
        all_diffs += kafka_diffs
    
    all_actions = aws_actions + k8s_actions
    if kafka_enabled:
        all_actions += kafka_actions
    
    reporter.report(all_diffs, all_actions)
    
    logger.info("DriftGuard completed successfully.")

if __name__ == "__main__":
    main()