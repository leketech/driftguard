#!/usr/bin/env python3
# Build timestamp: 2025-12-29-09-30-00
"""
DriftGuard - Autonomous Infrastructure Drift Detection and Self-Healing System

This module serves as the main entry point for the DriftGuard application.
It can run in two modes:
1. Continuous mode (for Deployment) - runs drift detection on a schedule
2. One-time mode (for CronJob) - runs drift detection once and exits
"""

import os
import sys
import time
import logging
import threading
import schedule
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import required modules
try:
    from config_loader import load_config
    from detectors.aws_detector import AWSDetector
    from detectors.k8s_detector import K8sDetector
    from detectors.kafka_detector import KafkaDetector
    from diff_analyzer import DiffAnalyzer
    from policy_engine import PolicyEngine
    from reporter import Reporter
    from monitoring import DriftGuardMonitoring
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

# Initialize monitoring
monitoring = DriftGuardMonitoring()

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks and metrics"""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'OK - DriftGuard is running')
        elif self.path == '/ready':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'OK - DriftGuard is ready')
        elif self.path == '/metrics':
            from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
            self.send_response(200)
            self.send_header('Content-type', CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        else:
            self.send_response(404)
            self.end_headers()

def run_drift_detection():
    """Run a single cycle of drift detection"""
    import time
    start_time = time.time()

    try:
        logger.info("Starting DriftGuard drift detection cycle...")
        monitoring.set_agent_status(True)
        monitoring.set_agent_info(version="1.0.0", config_hash="placeholder")

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
                logger.error(f"Failed to initialize Kafka detector: {e}")
                monitoring.record_error('kafka_init_error', 'kafka_detector')
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
        start_time_diff = time.time()
        aws_diffs = diff_analyzer.compute_diffs(desired_aws_state, live_aws_state)
        monitoring.record_scrape_duration('aws', time.time() - start_time_diff)

        start_time_diff = time.time()
        k8s_diffs = diff_analyzer.compute_diffs(desired_k8s_state, live_k8s_state)
        monitoring.record_scrape_duration('k8s', time.time() - start_time_diff)

        if kafka_enabled:
            start_time_diff = time.time()
            kafka_diffs = diff_analyzer.compute_diffs(desired_kafka_state, live_kafka_state)
            monitoring.record_scrape_duration('kafka', time.time() - start_time_diff)
        else:
            kafka_diffs = []

        # Count drift events
        for diff in aws_diffs:
            severity = getattr(diff, 'severity', 'unknown')
            if hasattr(severity, 'value'):
                severity = severity.value
            resource_type = getattr(diff, 'resource_type', 'unknown')
            monitoring.record_drift(resource_type, severity)
                
        for diff in k8s_diffs:
            severity = getattr(diff, 'severity', 'unknown')
            if hasattr(severity, 'value'):
                severity = severity.value
            resource_type = getattr(diff, 'resource_type', 'unknown')
            monitoring.record_drift(resource_type, severity)
                
        if kafka_enabled:
            for diff in kafka_diffs:
                severity = getattr(diff, 'severity', 'unknown')
                if hasattr(severity, 'value'):
                    severity = severity.value
                resource_type = getattr(diff, 'resource_type', 'unknown')
                monitoring.record_drift(resource_type, severity)

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
                resource_type = getattr(action, 'resource_type', 'unknown')
                status = getattr(action, 'status', 'unknown')
                monitoring.record_remediation(resource_type, status)

        # Combine all diffs and actions into a single report
        logger.info("Reporting results...")
        all_diffs = aws_diffs + k8s_diffs
        if kafka_enabled:
            all_diffs += kafka_diffs

        all_actions = aws_actions + k8s_actions
        if kafka_enabled:
            all_actions += kafka_actions

        reporter.report(all_diffs, all_actions)

        # Record total run duration
        total_duration = time.time() - start_time
        monitoring.record_run_duration(total_duration)
        monitoring.state['last_run_duration'] = total_duration
        monitoring.update_last_run('success', time.time())

        # Evaluate and log alerts
        alerts = monitoring.evaluate_alerts()
        if alerts:
            logger.warning(f"Active alerts: {len(alerts)}")
            for alert in alerts:
                logger.warning(f"Alert: {alert['name']} - {alert['description']}")

        logger.info(f"DriftGuard completed successfully in {total_duration:.2f}s.")

    except Exception as e:
        logger.error(f"DriftGuard failed with error: {e}", exc_info=True)
        monitoring.record_error('main_error', 'main')
        monitoring.update_last_run('error', time.time())
        monitoring.set_agent_status(False)
        # Don't exit in continuous mode, just log the error and continue

def run_scheduler():
    """Run the scheduler in a separate thread"""
    # Get the interval from environment variable or default to 30 minutes
    interval_minutes = int(os.getenv('DRIFT_DETECTION_INTERVAL', '30'))
    schedule.every(interval_minutes).minutes.do(run_drift_detection)
    
    logger.info(f"Starting scheduler with {interval_minutes}-minute intervals")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_health_server():
    """Start the health check server in a separate thread"""
    port = int(os.getenv('HEALTH_CHECK_PORT', '8000'))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Starting health check server on port {port}")
    server.serve_forever()

def main():
    """Main entry point for DriftGuard"""
    # Determine mode: continuous (Deployment) or one-time (CronJob)
    run_mode = os.getenv('RUN_MODE', 'continuous').lower()
    
    if run_mode == 'continuous':
        logger.info("Starting DriftGuard in continuous mode...")
        
        # Start health check server in a separate thread
        health_thread = threading.Thread(target=start_health_server, daemon=True)
        health_thread.start()
        
        # Start the scheduler in the main thread
        run_scheduler()
    else:
        # One-time execution mode (for CronJob compatibility)
        logger.info("Starting DriftGuard in one-time mode...")
        run_drift_detection()
        logger.info("DriftGuard completed one-time execution.")

if __name__ == "__main__":
    main()