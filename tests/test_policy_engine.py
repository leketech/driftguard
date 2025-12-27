#!/usr/bin/env python3
"""
Unit tests for DriftGuard policy engine
"""

import unittest
import tempfile
import os
from unittest.mock import patch, mock_open
from agent.policy_engine import PolicyEngine
from agent.models import DriftReport, DriftType, DriftSeverity

class TestPolicyEngine(unittest.TestCase):
    """Test cases for policy engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_policies = """
remediation:
  auto_apply:
    - environment: dev
      namespaces: ["default", "staging"]
      resources:
        - "*"
    - environment: prod
      namespaces: []
      resources: []
drift_rules:
  ignore:
    - aws_instance.tags.Terraform
    - k8s_pod.status.hostIP
  critical:
    - aws_security_group.ingress
    - k8s_deployment.spec.template.spec.containers.image
"""
        
        # Create a temporary file for policies
        self.temp_dir = tempfile.mkdtemp()
        self.policy_file = os.path.join(self.temp_dir, "policies.yaml")
        with open(self.policy_file, 'w') as f:
            f.write(self.test_policies)
        
        # Mock config
        self.config = {"policy_file": self.policy_file}
        
        # Create policy engine
        with patch("builtins.open", mock_open(read_data=self.test_policies)):
            with patch("yaml.safe_load", return_value={
                "remediation": {
                    "auto_apply": [
                        {"environment": "dev", "namespaces": ["default", "staging"], "resources": ["*"]},
                        {"environment": "prod", "namespaces": [], "resources": []}
                    ]
                },
                "drift_rules": {
                    "ignore": ["aws_instance.tags.Terraform", "k8s_pod.status.hostIP"],
                    "critical": ["aws_security_group.ingress", "k8s_deployment.spec.template.spec.containers.image"]
                }
            }):
                self.policy_engine = PolicyEngine(self.config)

    def test_classify_severity_ignored(self):
        """Test classifying drift as ignored"""
        report = DriftReport(
            resource_type="aws_instance",
            resource_id="i-1234567890abcdef0",
            drift_type=DriftType.AWS,
            field_path="tags.Terraform",
            expected_value="true",
            actual_value="false",
            severity=DriftSeverity.WARNING,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        severity = self.policy_engine._classify_severity(report)
        self.assertEqual(severity, DriftSeverity.IGNORED)

    def test_classify_severity_critical(self):
        """Test classifying drift as critical"""
        report = DriftReport(
            resource_type="aws_security_group",
            resource_id="sg-12345678",
            drift_type=DriftType.AWS,
            field_path="ingress",
            expected_value="[80, 443]",
            actual_value="[80, 443, 22]",
            severity=DriftSeverity.WARNING,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        severity = self.policy_engine._classify_severity(report)
        self.assertEqual(severity, DriftSeverity.CRITICAL)

    def test_classify_severity_warning(self):
        """Test classifying drift as warning (default)"""
        report = DriftReport(
            resource_type="aws_instance",
            resource_id="i-1234567890abcdef0",
            drift_type=DriftType.AWS,
            field_path="instance_type",
            expected_value="t2.micro",
            actual_value="t2.large",
            severity=DriftSeverity.WARNING,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        severity = self.policy_engine._classify_severity(report)
        self.assertEqual(severity, DriftSeverity.WARNING)

if __name__ == '__main__':
    unittest.main()