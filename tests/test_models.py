#!/usr/bin/env python3
"""
Unit tests for DriftGuard models
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.models import DriftSeverity, DriftType, DriftReport, RemediationAction, Config

class TestModels(unittest.TestCase):
    """Test cases for DriftGuard data models"""

    def test_drift_severity_enum(self):
        """Test DriftSeverity enum values"""
        self.assertEqual(DriftSeverity.SAFE.value, "safe")
        self.assertEqual(DriftSeverity.WARNING.value, "warning")
        self.assertEqual(DriftSeverity.CRITICAL.value, "critical")
        self.assertEqual(DriftSeverity.IGNORED.value, "ignored")

    def test_drift_type_enum(self):
        """Test DriftType enum values"""
        self.assertEqual(DriftType.AWS.value, "aws")
        self.assertEqual(DriftType.KUBERNETES.value, "kubernetes")

    def test_drift_report_model(self):
        """Test DriftReport model creation"""
        report = DriftReport(
            drift_id="test-drift-id-1",
            resource_type="aws_instance",
            resource_id="i-1234567890abcdef0",
            drift_type=DriftType.AWS,
            field_path="instance_type",
            expected_value="t2.micro",
            actual_value="t2.large",
            severity=DriftSeverity.WARNING,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        self.assertEqual(report.resource_type, "aws_instance")
        self.assertEqual(report.resource_id, "i-1234567890abcdef0")
        self.assertEqual(report.drift_type, DriftType.AWS)
        self.assertEqual(report.field_path, "instance_type")
        self.assertEqual(report.expected_value, "t2.micro")
        self.assertEqual(report.actual_value, "t2.large")
        self.assertEqual(report.severity, DriftSeverity.WARNING)

    def test_remediation_action_model(self):
        """Test RemediationAction model creation"""
        action = RemediationAction(
            action_type="remediate",
            resource_type="aws_instance",
            resource_id="i-1234567890abcdef0",
            description="Change instance type from t2.large to t2.micro",
            auto_apply=True,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        self.assertEqual(action.action_type, "remediate")
        self.assertEqual(action.resource_type, "aws_instance")
        self.assertEqual(action.resource_id, "i-1234567890abcdef0")
        self.assertEqual(action.description, "Change instance type from t2.large to t2.micro")
        self.assertTrue(action.auto_apply)

if __name__ == '__main__':
    unittest.main()