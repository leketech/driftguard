#!/usr/bin/env python3
"""
Custom rules for DriftGuard
This file demonstrates how to extend DriftGuard with custom rules.
"""

from typing import List
from agent.models import DriftReport, DriftSeverity

def evaluate_custom_rules(drift_report: DriftReport) -> DriftSeverity:
    """
    Example custom rule evaluator
    
    Args:
        drift_report: The drift report to evaluate
        
    Returns:
        DriftSeverity: The evaluated severity level
    """
    # Example custom rule: Flag any drift in production namespaces as critical
    if "prod" in drift_report.resource_id.lower():
        return DriftSeverity.CRITICAL
    
    # Example custom rule: Flag any security group changes as warning
    if "security_group" in drift_report.resource_type.lower():
        return DriftSeverity.WARNING
    
    # Default: return the existing severity
    return drift_report.severity

def get_custom_ignore_patterns() -> List[str]:
    """
    Example function to return custom ignore patterns
    
    Returns:
        List[str]: List of patterns to ignore
    """
    return [
        # Ignore changes to auto-generated timestamps
        "*.last_modified",
        # Ignore changes to provider-specific fields
        "*.provider_*"
    ]