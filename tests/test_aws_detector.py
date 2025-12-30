#!/usr/bin/env python3
"""
Unit tests for DriftGuard AWS detector
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.detectors.aws_detector import AWSDetector


class TestAWSDetector(unittest.TestCase):
    """Test cases for AWS detector functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'git': {
                'repo_url': 'https://github.com/test/repo.git',
                'branch': 'main'
            },
            'aws': {
                'region': 'us-east-1',
                'account_id': '123456789012',
                'terraform_state_key': 'terraform/state.tfstate'
            },
            'github': {
                'token': 'test-token'
            }
        }
        self.aws_detector = AWSDetector(self.config)

    def test_init(self):
        """Test initialization of AWS detector"""
        self.assertEqual(self.aws_detector.aws_region, 'us-east-1')
        self.assertEqual(self.aws_detector.aws_account_id, '123456789012')
        self.assertEqual(self.aws_detector.terraform_state_key, 'terraform/state.tfstate')

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.loads')
    @patch('os.chdir')
    @patch('tempfile.mkdtemp')
    def test_get_desired_state_success(self, mock_mkdtemp, mock_chdir, mock_json_loads, mock_open, mock_subprocess):
        """Test successful retrieval of desired state from Terraform"""
        # Mock Terraform state JSON
        mock_terraform_state = {
            'values': {
                'root_module': {
                    'resources': [
                        {
                            'type': 'aws_instance',
                            'name': 'test_instance',
                            'provider_name': 'aws',
                            'values': {'instance_type': 't2.micro'},
                            'address': 'aws_instance.test_instance',
                            'mode': 'managed'
                        }
                    ]
                }
            }
        }
        
        mock_mkdtemp.return_value = "/tmp/test_temp_dir"
        mock_json_loads.return_value = mock_terraform_state
        mock_subprocess.return_value = Mock(stdout='{"some": "json"}', stderr='', returncode=0)
        
        desired_state = self.aws_detector.get_desired_state()
        
        # Verify subprocess was called to initialize Terraform
        mock_subprocess.assert_called()
        # Verify the state was parsed correctly
        self.assertIn('resources', desired_state)
        self.assertEqual(len(desired_state['resources']), 1)
        self.assertEqual(desired_state['resources'][0]['type'], 'aws_instance')

    @patch('subprocess.run')
    @patch('os.chdir')
    @patch('tempfile.mkdtemp')
    def test_get_desired_state_terraform_error(self, mock_mkdtemp, mock_chdir, mock_subprocess):
        """Test error handling when Terraform command fails"""
        mock_mkdtemp.return_value = "/tmp/test_temp_dir"
        # Mock subprocess to raise CalledProcessError
        mock_subprocess.side_effect = [
            None,  # git clone
            Mock(returncode=1, stderr='Terraform init failed')  # terraform init
        ]
        
        with self.assertRaises(Exception):
            self.aws_detector.get_desired_state()

    @patch('subprocess.run')
    @patch('json.loads')
    @patch('os.chdir')
    @patch('tempfile.mkdtemp')
    def test_get_desired_state_json_error(self, mock_mkdtemp, mock_chdir, mock_json_loads, mock_subprocess):
        """Test error handling when JSON parsing fails"""
        mock_mkdtemp.return_value = "/tmp/test_temp_dir"
        # Mock json.loads to raise JSONDecodeError
        mock_json_loads.side_effect = ValueError("Invalid JSON")
        mock_subprocess.return_value = Mock(stdout='invalid json', stderr='', returncode=0)
        
        with self.assertRaises(ValueError):
            self.aws_detector.get_desired_state()

    @patch('boto3.client')
    def test_get_live_state_success(self, mock_boto3_client):
        """Test successful retrieval of live AWS state"""
        # Mock AWS clients and their responses
        mock_ec2_client = Mock()
        mock_ec2_client.describe_instances.return_value = {'Reservations': []}
        mock_ec2_client.describe_security_groups.return_value = {'SecurityGroups': []}
        
        mock_boto3_client.return_value = mock_ec2_client
        
        live_state = self.aws_detector.get_live_state()
        
        # Verify the AWS clients were called
        mock_ec2_client.describe_instances.assert_called_once()
        mock_ec2_client.describe_security_groups.assert_called_once()
        
        # Verify the returned state structure
        self.assertIn('ec2_instances', live_state)
        self.assertIn('security_groups', live_state)

    @patch('boto3.client')
    def test_parse_terraform_state_basic(self, mock_boto3_client):
        """Test basic Terraform state parsing"""
        terraform_state = {
            'values': {
                'root_module': {
                    'resources': [
                        {
                            'type': 'aws_instance',
                            'name': 'web_server',
                            'provider_name': 'aws',
                            'values': {'instance_type': 't2.micro', 'ami': 'ami-12345'},
                            'address': 'aws_instance.web_server',
                            'mode': 'managed'
                        }
                    ]
                }
            }
        }
        
        result = self.aws_detector._parse_terraform_state(terraform_state)
        
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 1)
        resource = result['resources'][0]
        self.assertEqual(resource['type'], 'aws_instance')
        self.assertEqual(resource['name'], 'web_server')
        self.assertEqual(resource['values']['instance_type'], 't2.micro')

    @patch('boto3.client')
    def test_parse_terraform_state_with_child_modules(self, mock_boto3_client):
        """Test Terraform state parsing with child modules"""
        terraform_state = {
            'values': {
                'root_module': {
                    'resources': [
                        {
                            'type': 'aws_vpc',
                            'name': 'main',
                            'provider_name': 'aws',
                            'values': {'cidr_block': '10.0.0.0/16'},
                            'address': 'aws_vpc.main',
                            'mode': 'managed'
                        }
                    ],
                    'child_modules': [
                        {
                            'resources': [
                                {
                                    'type': 'aws_subnet',
                                    'name': 'subnet1',
                                    'provider_name': 'aws',
                                    'values': {'cidr_block': '10.0.1.0/24'},
                                    'address': 'module.subnet.aws_subnet.subnet1',
                                    'mode': 'managed'
                                }
                            ]
                        }
                    ]
                }
            }
        }
        
        result = self.aws_detector._parse_terraform_state(terraform_state)
        
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 2)  # VPC + subnet
        
        resource_types = [res['type'] for res in result['resources']]
        self.assertIn('aws_vpc', resource_types)
        self.assertIn('aws_subnet', resource_types)

    @patch('boto3.client')
    def test_parse_terraform_state_with_outputs(self, mock_boto3_client):
        """Test Terraform state parsing with outputs"""
        terraform_state = {
            'values': {
                'root_module': {
                    'resources': []
                },
                'outputs': {
                    'vpc_id': {
                        'value': 'vpc-12345'
                    },
                    'public_subnet_ids': {
                        'value': ['subnet-abc', 'subnet-def']
                    }
                }
            }
        }
        
        result = self.aws_detector._parse_terraform_state(terraform_state)
        
        self.assertIn('outputs', result)
        self.assertEqual(result['outputs']['vpc_id'], 'vpc-12345')
        self.assertEqual(result['outputs']['public_subnet_ids'], ['subnet-abc', 'subnet-def'])

    @patch('boto3.client')
    def test_parse_terraform_state_empty(self, mock_boto3_client):
        """Test Terraform state parsing with empty state"""
        terraform_state = {
            'values': {
                'root_module': {
                    'resources': []
                }
            }
        }
        
        result = self.aws_detector._parse_terraform_state(terraform_state)
        
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 0)
        self.assertIn('outputs', result)
        self.assertEqual(len(result['outputs']), 0)

    @patch('boto3.client')
    def test_parse_terraform_state_missing_values(self, mock_boto3_client):
        """Test Terraform state parsing with missing values key"""
        terraform_state = {
            # Missing 'values' key
        }
        
        result = self.aws_detector._parse_terraform_state(terraform_state)
        
        self.assertIn('resources', result)
        self.assertEqual(len(result['resources']), 0)
        self.assertIn('outputs', result)
        self.assertEqual(len(result['outputs']), 0)


if __name__ == '__main__':
    unittest.main()