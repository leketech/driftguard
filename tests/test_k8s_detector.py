#!/usr/bin/env python3
"""
Unit tests for DriftGuard Kubernetes detector
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.detectors.k8s_detector import K8sDetector


class TestK8sDetector(unittest.TestCase):
    """Test cases for Kubernetes detector functionality"""

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
        self.k8s_detector = K8sDetector(self.config)

    def test_init(self):
        """Test initialization of Kubernetes detector"""
        # Just verify the detector was created successfully
        self.assertIsNotNone(self.k8s_detector)

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test-deployment")
    @patch('yaml.safe_load_all')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates(self, mock_mkdtemp, mock_yaml_load_all, mock_file, mock_os_walk, mock_subprocess):
        """Test parsing of Helm templates"""
        # Mock the YAML loading to return a deployment
        mock_yaml_load_all.return_value = [
            {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': 'test-deployment',
                    'namespace': 'default'
                },
                'spec': {
                    'replicas': 3
                }
            }
        ]
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return a YAML file
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['deployment.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        self.assertIn('deployments', result)
        self.assertEqual(len(result['deployments']), 1)
        self.assertEqual(result['deployments'][0]['metadata']['name'], 'test-deployment')

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="apiVersion: v1\nkind: Service\nmetadata:\n  name: test-service")
    @patch('yaml.safe_load_all')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_service(self, mock_mkdtemp, mock_yaml_load_all, mock_file, mock_os_walk, mock_subprocess):
        """Test parsing of Helm templates for services"""
        # Mock the YAML loading to return a service
        mock_yaml_load_all.return_value = [
            {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': 'test-service',
                    'namespace': 'default'
                },
                'spec': {
                    'ports': [{'port': 80}]
                }
            }
        ]
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return a YAML file
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['service.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        self.assertIn('services', result)
        self.assertEqual(len(result['services']), 1)
        self.assertEqual(result['services'][0]['metadata']['name'], 'test-service')

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test-configmap")
    @patch('yaml.safe_load_all')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_configmap(self, mock_mkdtemp, mock_yaml_load_all, mock_file, mock_os_walk, mock_subprocess):
        """Test parsing of Helm templates for configmaps"""
        # Mock the YAML loading to return a configmap
        mock_yaml_load_all.return_value = [
            {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': 'test-configmap',
                    'namespace': 'default'
                },
                'data': {
                    'key': 'value'
                }
            }
        ]
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return a YAML file
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['configmap.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        self.assertIn('configmaps', result)
        self.assertEqual(len(result['configmaps']), 1)
        self.assertEqual(result['configmaps'][0]['metadata']['name'], 'test-configmap')

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="invalid yaml content")
    @patch('yaml.safe_load_all')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_yaml_error(self, mock_mkdtemp, mock_yaml_load_all, mock_file, mock_os_walk, mock_subprocess):
        """Test error handling when YAML parsing fails"""
        # Mock yaml.safe_load_all to raise an exception
        mock_yaml_load_all.side_effect = Exception("YAML parsing error")
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return a YAML file
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['invalid.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        # This should not raise an exception, just return empty results
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        # Should return empty lists due to error
        self.assertIn('deployments', result)
        self.assertIn('services', result)
        self.assertIn('configmaps', result)
        self.assertEqual(len(result['deployments']), 0)
        self.assertEqual(len(result['services']), 0)
        self.assertEqual(len(result['configmaps']), 0)

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_no_yaml_files(self, mock_mkdtemp, mock_os_walk, mock_subprocess):
        """Test parsing when no YAML files are found"""
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return no YAML files
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['README.txt', 'chart.json'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        self.assertIn('deployments', result)
        self.assertIn('services', result)
        self.assertIn('configmaps', result)
        self.assertEqual(len(result['deployments']), 0)
        self.assertEqual(len(result['services']), 0)
        self.assertEqual(len(result['configmaps']), 0)

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('yaml.safe_load_all')
    @patch('builtins.open')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_multiple_files(self, mock_mkdtemp, mock_file, mock_yaml_load_all, mock_os_walk, mock_subprocess):
        """Test parsing multiple YAML files"""
        # Mock different content for each file
        def mock_open_side_effect(file_path, *args, **kwargs):
            if 'deployment1.yaml' in file_path:
                mock_file.return_value.read.return_value = '''apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test-deployment-1\n  namespace: default'''
                mock_yaml_load_all.return_value = [{
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'metadata': {
                        'name': 'test-deployment-1',
                        'namespace': 'default'
                    }
                }]
            elif 'deployment2.yaml' in file_path:
                mock_file.return_value.read.return_value = '''apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: test-deployment-2\n  namespace: default'''
                mock_yaml_load_all.return_value = [{
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'metadata': {
                        'name': 'test-deployment-2',
                        'namespace': 'default'
                    }
                }]
            return mock_file.return_value
        
        mock_file.side_effect = mock_open_side_effect
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return multiple YAML files
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['deployment1.yaml', 'deployment2.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        self.assertIn('deployments', result)
        self.assertEqual(len(result['deployments']), 2)
        names = [dep['metadata']['name'] for dep in result['deployments']]
        self.assertIn('test-deployment-1', names)
        self.assertIn('test-deployment-2', names)

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('yaml.safe_load_all')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_empty_file(self, mock_mkdtemp, mock_yaml_load_all, mock_file, mock_os_walk, mock_subprocess):
        """Test parsing when YAML file is empty"""
        # Mock yaml.safe_load_all to return None for empty content
        mock_yaml_load_all.return_value = [None]
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return a YAML file
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['empty.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        # Unknown kinds should not be added to any of the lists
        self.assertIn('deployments', result)
        self.assertIn('services', result)
        self.assertIn('configmaps', result)
        self.assertEqual(len(result['deployments']), 0)
        self.assertEqual(len(result['services']), 0)
        self.assertEqual(len(result['configmaps']), 0)

    @patch('subprocess.run')
    @patch('os.walk')
    @patch('builtins.open', new_callable=mock_open, read_data="apiVersion: apps/v1\nkind: UnknownKind\nmetadata:\n  name: test-unknown")
    @patch('yaml.safe_load_all')
    @patch('tempfile.mkdtemp')
    def test_parse_helm_templates_unknown_kind(self, mock_mkdtemp, mock_yaml_load_all, mock_file, mock_os_walk, mock_subprocess):
        """Test parsing when YAML contains unknown resource kind"""
        # Mock the YAML loading to return an unknown kind
        mock_yaml_load_all.return_value = [
            {
                'apiVersion': 'apps/v1',
                'kind': 'UnknownKind',
                'metadata': {
                    'name': 'test-unknown',
                    'namespace': 'default'
                }
            }
        ]
        
        mock_mkdtemp.return_value = '/tmp/test_temp_dir'
        # Mock os.walk to return a YAML file
        mock_os_walk.return_value = [
            ('/tmp/helm_templates_test', [], ['unknown.yaml'])
        ]
        
        helm_chart_dirs = ['/tmp/test-chart']
        temp_dir = '/tmp/test_temp_dir'
        
        result = self.k8s_detector._parse_helm_templates(helm_chart_dirs, temp_dir)
        
        # Unknown kinds should not be added to any of the lists
        self.assertIn('deployments', result)
        self.assertIn('services', result)
        self.assertIn('configmaps', result)
        self.assertEqual(len(result['deployments']), 0)
        self.assertEqual(len(result['services']), 0)
        self.assertEqual(len(result['configmaps']), 0)


if __name__ == '__main__':
    unittest.main()