#!/usr/bin/env python3
"""
Policy Engine for DriftGuard
"""

import yaml
import logging
from typing import List, Dict, Any
from .models import DriftReport, RemediationAction, DriftSeverity
import os

logger = logging.getLogger(__name__)

class PolicyEngine:
    """Engine for applying policies to drift reports"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.policies = self._load_policies()
    
    def _load_policies(self) -> Dict[str, Any]:
        """
        Load policies from configuration file
        
        Returns:
            Dictionary containing the policies
        """
        # Look for policies in both possible locations
        possible_paths = [
            "config/policies.yaml",
            "/app/config/policies.yaml",
            "driftguard/config/policies.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
        
        # If no file found, return default policies
        logger.warning("No policies file found, using default policies")
        return {
            "remediation": {
                "auto_apply": [
                    {"environment": "dev", "namespaces": ["default", "staging"], "resources": ["*"]}
                ]
            },
            "drift_rules": {
                "ignore": [],
                "critical": [],
                "warning": []
            }
        }
    
    def evaluate(self, drift_reports: List[DriftReport]) -> List[RemediationAction]:
        """
        Evaluate drift reports against policies and determine actions
        
        Args:
            drift_reports: List of DriftReport objects
            
        Returns:
            List of RemediationAction objects
        """
        logger.info("Evaluating drift reports against policies...")
        
        actions = []
        
        for report in drift_reports:
            # Classify severity based on policies
            severity = self._classify_severity(report)
            report.severity = severity
            
            # Determine action based on severity and environment
            action = self._determine_action(report)
            if action:
                actions.append(action)
        
        return actions
    
    def _classify_severity(self, report: DriftReport) -> DriftSeverity:
        """
        Classify the severity of a drift report based on policies
        
        Args:
            report: DriftReport object
            
        Returns:
            DriftSeverity enum value
        """
        # Check if the drift should be ignored
        ignore_patterns = self.policies.get('drift_rules', {}).get('ignore', [])
        for pattern in ignore_patterns:
            if pattern in f"{report.resource_type}.{report.field_path}":
                return DriftSeverity.IGNORED
        
        # Check if the drift is critical
        critical_patterns = self.policies.get('drift_rules', {}).get('critical', [])
        for pattern in critical_patterns:
            if pattern in f"{report.resource_type}.{report.field_path}":
                return DriftSeverity.CRITICAL
        
        # Default to warning
        return DriftSeverity.WARNING
    
    def _determine_action(self, report: DriftReport) -> RemediationAction:
        """
        Determine the appropriate action for a drift report
        
        Args:
            report: DriftReport object
            
        Returns:
            RemediationAction object or None
        """
        # Check if auto-apply is enabled for this environment
        auto_apply_rules = self.policies.get('remediation', {}).get('auto_apply', [])
        
        # Simplified logic - in reality, you'd check the specific environment
        auto_apply = False
        for rule in auto_apply_rules:
            if rule['environment'] == 'dev':
                auto_apply = True
                break
        
        # Create action
        action = RemediationAction(
            action_type="remediate" if auto_apply else "alert",
            resource_type=report.resource_type,
            resource_id=report.resource_id,
            description=f"Drift detected in {report.resource_type}.{report.field_path}",
            auto_apply=auto_apply,
            timestamp=report.timestamp
        )
        
        return action