#!/usr/bin/env python3
"""
Monitoring and Alerting module for DriftGuard
Provides enhanced monitoring capabilities and alerting mechanisms
"""

import logging
from typing import Dict, Any, List
from prometheus_client import Counter, Histogram, Gauge, Info
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Data class for alert information"""
    name: str
    severity: AlertSeverity
    description: str
    labels: Dict[str, str]
    value: float = 0.0


class DriftGuardMonitoring:
    """Enhanced monitoring and alerting for DriftGuard"""

    def __init__(self):
        # Initialize Prometheus metrics
        self._init_metrics()
        
        # Store alert definitions
        self.alerts: List[Alert] = []
        
        # Track state for alert conditions
        self.state = {
            'last_drift_count': 0,
            'last_error_count': 0,
            'last_run_duration': 0.0
        }

    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY
        import prometheus_client
            
        # Check if metrics already exist in the registry
        existing_metrics = [metric.name for metric in REGISTRY.collect()]
            
        # Core drift metrics
        metric_name = 'driftguard_drift_total'
        if metric_name not in existing_metrics:
            self.drift_total = Counter(
                metric_name, 
                'Total drift events detected',
                labelnames=['resource_type', 'severity']
            )
        else:
            # If metric already exists, we'll get it from registry
            # For now, we'll just log that it exists
            import logging
            logger.info(f"Metric {metric_name} already exists")
            
        metric_name = 'driftguard_drift_by_severity'
        if metric_name not in existing_metrics:
            self.drift_by_severity = Counter(
                metric_name, 
                'Drift by severity',
                labelnames=['severity']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        metric_name = 'driftguard_drift_by_resource'
        if metric_name not in existing_metrics:
            self.drift_by_resource = Counter(
                metric_name, 
                'Drift by resource type',
                labelnames=['resource_type']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        # Remediation metrics
        metric_name = 'driftguard_remediation_attempts_total'
        if metric_name not in existing_metrics:
            self.remediation_attempts = Counter(
                metric_name, 
                'Remediation attempts',
                labelnames=['resource_type', 'status']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        metric_name = 'driftguard_remediation_success_total'
        if metric_name not in existing_metrics:
            self.remediation_success = Counter(
                metric_name, 
                'Successful remediations',
                labelnames=['resource_type']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        # Performance metrics
        metric_name = 'driftguard_scrape_duration_seconds'
        if metric_name not in existing_metrics:
            self.scrape_duration = Histogram(
                metric_name, 
                'Scrape and compare duration',
                labelnames=['resource_type']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        metric_name = 'driftguard_run_duration_seconds'
        if metric_name not in existing_metrics:
            self.run_duration = Histogram(
                metric_name,
                'Total run duration'
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        # Error metrics
        metric_name = 'driftguard_errors_total'
        if metric_name not in existing_metrics:
            self.errors_total = Counter(
                metric_name,
                'Total errors encountered',
                labelnames=['error_type', 'component']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        # Agent info
        metric_name = 'driftguard_agent_info'
        if metric_name not in existing_metrics:
            self.agent_info = Info(metric_name, 'Agent information')
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        # Status gauges
        metric_name = 'driftguard_agent_running'
        if metric_name not in existing_metrics:
            self.agent_running = Gauge(metric_name, 'Agent running status')
        else:
            logger.info(f"Metric {metric_name} already exists")
            
        metric_name = 'driftguard_last_run_timestamp'
        if metric_name not in existing_metrics:
            self.last_run_timestamp = Gauge(
                metric_name, 
                'Last run timestamp',
                labelnames=['status']
            )
        else:
            logger.info(f"Metric {metric_name} already exists")

    def record_drift(self, resource_type: str, severity: str):
        """Record a drift event"""
        try:
            self.drift_total.labels(resource_type=resource_type, severity=severity).inc()
            self.drift_by_severity.labels(severity=severity).inc()
            self.drift_by_resource.labels(resource_type=resource_type).inc()
            
            # Update state for alerting
            self.state['last_drift_count'] += 1
            
            logger.debug(f"Recorded drift: {resource_type} with severity {severity}")
        except Exception as e:
            logger.error(f"Error recording drift: {e}")
            self.errors_total.labels(error_type='recording_error', component='monitoring').inc()

    def record_remediation(self, resource_type: str, status: str):
        """Record a remediation event"""
        try:
            self.remediation_attempts.labels(resource_type=resource_type, status=status).inc()
            
            if status == 'success':
                self.remediation_success.labels(resource_type=resource_type).inc()
            
            logger.debug(f"Recorded remediation: {resource_type} with status {status}")
        except Exception as e:
            logger.error(f"Error recording remediation: {e}")
            self.errors_total.labels(error_type='recording_error', component='monitoring').inc()

    def record_scrape_duration(self, resource_type: str, duration: float):
        """Record scrape duration"""
        try:
            self.scrape_duration.labels(resource_type=resource_type).observe(duration)
            logger.debug(f"Recorded scrape duration: {duration}s for {resource_type}")
        except Exception as e:
            logger.error(f"Error recording scrape duration: {e}")
            self.errors_total.labels(error_type='recording_error', component='monitoring').inc()

    def record_run_duration(self, duration: float):
        """Record total run duration"""
        try:
            self.run_duration.observe(duration)
            logger.debug(f"Recorded run duration: {duration}s")
        except Exception as e:
            logger.error(f"Error recording run duration: {e}")
            self.errors_total.labels(error_type='recording_error', component='monitoring').inc()

    def record_error(self, error_type: str, component: str):
        """Record an error"""
        try:
            self.errors_total.labels(error_type=error_type, component=component).inc()
            self.state['last_error_count'] += 1
            
            logger.warning(f"Recorded error: {error_type} in {component}")
        except Exception as e:
            logger.error(f"Error recording error (meta-error): {e}")

    def set_agent_info(self, version: str, config_hash: str):
        """Set agent information"""
        try:
            self.agent_info.info({
                'version': version,
                'config_hash': config_hash,
                'status': 'running'
            })
            logger.debug(f"Set agent info: v{version}")
        except Exception as e:
            logger.error(f"Error setting agent info: {e}")

    def set_agent_status(self, is_running: bool):
        """Set agent running status"""
        try:
            self.agent_running.set(1 if is_running else 0)
            logger.debug(f"Set agent status: {'running' if is_running else 'stopped'}")
        except Exception as e:
            logger.error(f"Error setting agent status: {e}")

    def update_last_run(self, status: str, timestamp: float):
        """Update last run timestamp"""
        try:
            # Reset all status labels to 0
            for s in ['success', 'error', 'warning']:
                self.last_run_timestamp.labels(status=s).set(0 if s != status else timestamp)
            
            logger.debug(f"Updated last run timestamp: {timestamp} with status {status}")
        except Exception as e:
            logger.error(f"Error updating last run: {e}")

    def evaluate_alerts(self) -> List[Dict[str, Any]]:
        """
        Evaluate alert conditions and return active alerts
        
        Returns:
            List of active alerts
        """
        active_alerts = []
        
        # Example alert: High drift rate
        if self.state['last_drift_count'] > 10:  # More than 10 drifts in the last run
            active_alerts.append({
                'name': 'HighDriftRate',
                'severity': AlertSeverity.HIGH.value,
                'description': f'High drift rate detected: {self.state["last_drift_count"]} drifts in last run',
                'labels': {'drift_count': str(self.state['last_drift_count'])},
                'generatorURL': 'https://github.com/leketech/driftguard/wiki/Alerts#high-drift-rate'
            })
        
        # Example alert: Agent errors
        if self.state['last_error_count'] > 5:  # More than 5 errors in the last run
            active_alerts.append({
                'name': 'HighErrorRate',
                'severity': AlertSeverity.CRITICAL.value,
                'description': f'High error rate detected: {self.state["last_error_count"]} errors in last run',
                'labels': {'error_count': str(self.state['last_error_count'])},
                'generatorURL': 'https://github.com/leketech/driftguard/wiki/Alerts#high-error-rate'
            })
        
        # Example alert: Long run duration
        if self.state['last_run_duration'] > 300:  # More than 5 minutes
            active_alerts.append({
                'name': 'LongRunDuration',
                'severity': AlertSeverity.MEDIUM.value,
                'description': f'Long run duration: {self.state["last_run_duration"]:.2f}s',
                'labels': {'duration_seconds': str(self.state['last_run_duration'])},
                'generatorURL': 'https://github.com/leketech/driftguard/wiki/Alerts#long-run-duration'
            })
        
        logger.info(f"Evaluated alerts, found {len(active_alerts)} active alerts")
        return active_alerts

    def add_custom_alert(self, alert: Alert):
        """Add a custom alert definition"""
        self.alerts.append(alert)
        logger.debug(f"Added custom alert: {alert.name}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of key metrics for logging"""
        return {
            'drift_total': self.state['last_drift_count'],
            'errors_total': self.state['last_error_count'],
            'last_run_duration': self.state['last_run_duration']
        }


# Global monitoring instance is created in main.py to avoid import-time instantiation