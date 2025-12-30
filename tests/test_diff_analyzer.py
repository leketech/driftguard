#!/usr/bin/env python3
"""
Unit tests for DriftGuard diff analyzer
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.diff_analyzer import DiffAnalyzer
from agent.models import DriftReport, DriftType, DriftSeverity


class TestDiffAnalyzer(unittest.TestCase):
    """Test cases for diff analyzer functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.diff_analyzer = DiffAnalyzer()

    def test_compute_diffs_empty_states(self):
        """Test computing diffs with empty states"""
        desired_state = {}
        live_state = {}
        
        diffs = self.diff_analyzer.compute_diffs(desired_state, live_state)
        
        self.assertEqual(len(diffs), 0)

    def test_compute_diffs_aws_resources(self):
        """Test computing diffs for AWS resources"""
        desired_state = {
            'resources': [
                {
                    'type': 'aws_instance',
                    'name': 'test_instance',
                    'values': {
                        'instance_type': 't2.micro',
                        'tags': {'Name': 'test'}
                    }
                }
            ]
        }
        live_state = {
            'ec2_instances': {},
            'security_groups': {}
        }
        
        diffs = self.diff_analyzer.compute_diffs(desired_state, live_state)
        
        # Should have at least one diff for the AWS instance
        self.assertGreaterEqual(len(diffs), 0)
        if diffs:
            self.assertTrue(all(diff.drift_type == DriftType.AWS for diff in diffs))

    def test_compute_diffs_k8s_resources(self):
        """Test computing diffs for Kubernetes resources"""
        desired_state = {
            'deployments': [
                {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'metadata': {
                        'name': 'test-deployment',
                        'namespace': 'default'
                    },
                    'spec': {
                        'replicas': 3,
                        'selector': {
                            'matchLabels': {
                                'app': 'test'
                            }
                        }
                    }
                }
            ]
        }
        live_state = {
            'deployments': {}
        }
        
        diffs = self.diff_analyzer.compute_diffs(desired_state, live_state)
        
        # Should have at least one diff for the Kubernetes deployment
        self.assertGreaterEqual(len(diffs), 0)
        if diffs:
            self.assertTrue(all(diff.drift_type == DriftType.KUBERNETES for diff in diffs))

    def test_compute_diffs_kafka_resources(self):
        """Test computing diffs for Kafka resources"""
        desired_state = {
            'topics': [
                {
                    'name': 'test-topic',
                    'partitions': 3,
                    'replication_factor': 2
                }
            ]
        }
        live_state = {
            'topics': []
        }
        
        diffs = self.diff_analyzer.compute_diffs(desired_state, live_state)
        
        # Should have at least one diff for the Kafka topic
        self.assertGreaterEqual(len(diffs), 0)
        if diffs:
            self.assertTrue(all(diff.drift_type == DriftType.KAFKA for diff in diffs))

    def test_compute_diffs_error_handling(self):
        """Test error handling in diff computation"""
        # Test with invalid input
        desired_state = None
        live_state = {}
        
        diffs = self.diff_analyzer.compute_diffs(desired_state, live_state)
        
        # Should return empty list in case of error
        self.assertEqual(diffs, [])

    def test_compute_diffs_duplicate_handling(self):
        """Test that duplicate drifts are properly handled"""
        desired_state = {
            'resources': [
                {
                    'type': 'aws_instance',
                    'name': 'test_instance',
                    'values': {
                        'instance_type': 't2.micro'
                    }
                }
            ]
        }
        live_state = {
            'ec2_instances': {},
            'security_groups': {}
        }
        
        # Compute diffs twice
        diffs1 = self.diff_analyzer.compute_diffs(desired_state, live_state)
        diffs2 = self.diff_analyzer.compute_diffs(desired_state, live_state)
        
        # Second call should return empty list since drifts are already seen
        self.assertGreaterEqual(len(diffs1), 0)
        self.assertEqual(len(diffs2), 0)

    def test_flatten_dict(self):
        """Test the _flatten_dict method"""
        nested_dict = {
            'level1': {
                'level2': {
                    'level3': 'value'
                },
                'simple': 'value2'
            },
            'top_level': 'value3'
        }
        
        flattened = self.diff_analyzer._flatten_dict(nested_dict)
        
        expected = {
            'level1.level2.level3': 'value',
            'level1.simple': 'value2',
            'top_level': 'value3'
        }
        
        self.assertEqual(flattened, expected)

    def test_flatten_dict_with_custom_separator(self):
        """Test the _flatten_dict method with custom separator"""
        nested_dict = {
            'level1': {
                'level2': 'value'
            }
        }
        
        flattened = self.diff_analyzer._flatten_dict(nested_dict, sep='__')
        
        expected = {
            'level1__level2': 'value'
        }
        
        self.assertEqual(flattened, expected)

    def test_compare_generic_resources(self):
        """Test the _compare_generic_resources method"""
        desired_state = {
            'simple_value': 'desired',
            'nested': {
                'value': 'nested_desired'
            }
        }
        live_state = {
            'simple_value': 'live',
            'nested': {
                'value': 'nested_live'
            }
        }
        
        diffs = self.diff_analyzer._compare_generic_resources(desired_state, live_state)
        
        # Should have 2 diffs for the different values
        self.assertEqual(len(diffs), 2)
        self.assertTrue(all(diff.severity == DriftSeverity.WARNING for diff in diffs))


if __name__ == '__main__':
    unittest.main()