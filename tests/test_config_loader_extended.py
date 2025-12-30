#!/usr/bin/env python3
"""
Extended unit tests for DriftGuard configuration loader
"""

import unittest
import os
import tempfile
from unittest.mock import patch, mock_open
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.config_loader import load_config, validate_config


class TestConfigLoaderExtended(unittest.TestCase):
    """Extended test cases for configuration loading and validation"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary config file for testing
        self.test_config_content = """
git:
  repo_url: "https://github.com/test/repo.git"
  branch: "main"
aws:
  region: "us-east-1"
  account_id: "123456789012"
  terraform_state_key: "terraform/state.tfstate"
github:
  token: "test-token"
logging:
  level: "INFO"
  format: "json"
  output: "stdout"
output:
  format: "json"
  destination: "stdout"
kafka:
  bootstrap_servers: "localhost:9092"
  security_protocol: "PLAINTEXT"
  consumer_group: "driftguard-test"
"""

    def test_load_config_with_valid_file(self):
        """Test loading configuration from a valid file"""
        with patch("builtins.open", mock_open(read_data=self.test_config_content)):
            with patch("os.path.exists", return_value=True):
                config = load_config("config/config.yaml")
                
                self.assertEqual(config['git']['repo_url'], "https://github.com/test/repo.git")
                self.assertEqual(config['git']['branch'], "main")
                self.assertEqual(config['aws']['region'], "us-east-1")
                self.assertEqual(config['aws']['account_id'], "123456789012")
                self.assertEqual(config['aws']['terraform_state_key'], "terraform/state.tfstate")
                self.assertEqual(config['github']['token'], "test-token")

    @patch.dict(os.environ, {
        "GIT_REPO_URL": "https://github.com/env/repo.git",
        "GIT_BRANCH": "develop",
        "AWS_REGION": "us-west-2",
        "AWS_ACCOUNT_ID": "987654321098",
        "TERRAFORM_STATE_KEY": "env/state.tfstate",
        "GITHUB_TOKEN": "env-token"
    })
    def test_load_config_with_env_override(self):
        """Test loading configuration with environment variable overrides"""
        with patch("builtins.open", mock_open(read_data=self.test_config_content)):
            with patch("os.path.exists", return_value=True):
                config = load_config("config/config.yaml")
                
                # Environment variables should override config file values
                self.assertEqual(config['git']['repo_url'], "https://github.com/env/repo.git")
                self.assertEqual(config['git']['branch'], "develop")
                self.assertEqual(config['aws']['region'], "us-west-2")
                self.assertEqual(config['aws']['account_id'], "987654321098")
                self.assertEqual(config['aws']['terraform_state_key'], "env/state.tfstate")
                self.assertEqual(config['github']['token'], "env-token")

    def test_validate_config_valid(self):
        """Test validation of a valid configuration"""
        valid_config = {
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
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        # Should not raise any exceptions
        validate_config(valid_config)

    def test_validate_config_missing_git_repo_url(self):
        """Test validation fails when git repo URL is missing"""
        invalid_config = {
            'git': {
                'repo_url': '',  # Empty
                'branch': 'main'
            },
            'aws': {
                'region': 'us-east-1',
                'account_id': '123456789012',
                'terraform_state_key': 'terraform/state.tfstate'
            },
            'github': {
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("Git repository URL is required", str(context.exception))

    def test_validate_config_missing_git_branch(self):
        """Test validation fails when git branch is missing"""
        invalid_config = {
            'git': {
                'repo_url': 'https://github.com/test/repo.git',
                'branch': ''  # Empty
            },
            'aws': {
                'region': 'us-east-1',
                'account_id': '123456789012',
                'terraform_state_key': 'terraform/state.tfstate'
            },
            'github': {
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("Git branch is required", str(context.exception))

    def test_validate_config_invalid_git_values(self):
        """Test validation fails when git values are invalid"""
        invalid_config = {
            'git': {
                'repo_url': 123,  # Not a string
                'branch': 'main'
            },
            'aws': {
                'region': 'us-east-1',
                'account_id': '123456789012',
                'terraform_state_key': 'terraform/state.tfstate'
            },
            'github': {
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("Git repository URL must be a non-empty string", str(context.exception))

    def test_validate_config_missing_aws_region(self):
        """Test validation fails when AWS region is missing"""
        invalid_config = {
            'git': {
                'repo_url': 'https://github.com/test/repo.git',
                'branch': 'main'
            },
            'aws': {
                'region': '',  # Empty
                'account_id': '123456789012',
                'terraform_state_key': 'terraform/state.tfstate'
            },
            'github': {
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("AWS region is required", str(context.exception))

    def test_validate_config_missing_aws_account_id(self):
        """Test validation fails when AWS account ID is missing"""
        invalid_config = {
            'git': {
                'repo_url': 'https://github.com/test/repo.git',
                'branch': 'main'
            },
            'aws': {
                'region': 'us-east-1',
                'account_id': '',  # Empty
                'terraform_state_key': 'terraform/state.tfstate'
            },
            'github': {
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("AWS account ID is required", str(context.exception))

    def test_validate_config_missing_terraform_state_key(self):
        """Test validation fails when Terraform state key is missing"""
        invalid_config = {
            'git': {
                'repo_url': 'https://github.com/test/repo.git',
                'branch': 'main'
            },
            'aws': {
                'region': 'us-east-1',
                'account_id': '123456789012',
                'terraform_state_key': ''  # Empty
            },
            'github': {
                'token': 'test-token'
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("Terraform state key is required", str(context.exception))

    def test_validate_config_invalid_output_destination(self):
        """Test validation fails when output destination is invalid"""
        invalid_config = {
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
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'invalid_destination'  # Invalid
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("is not valid. Must be one of: stdout, s3, file", str(context.exception))

    def test_validate_config_invalid_log_level(self):
        """Test validation fails when log level is invalid"""
        invalid_config = {
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
            },
            'logging': {
                'level': 'INVALID_LEVEL'  # Invalid
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            validate_config(invalid_config)
        
        self.assertIn("is not valid. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL", str(context.exception))

    def test_validate_config_warns_missing_github_token(self):
        """Test validation warns when GitHub token is missing"""
        config_without_token = {
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
                'token': ''  # Empty
            },
            'logging': {
                'level': 'INFO'
            },
            'output': {
                'destination': 'stdout'
            }
        }
        
        # Should not raise an exception, but should log a warning
        # We can't easily test the warning without patching the logger
        try:
            validate_config(config_without_token)
        except ValueError:
            self.fail("validate_config should not raise an exception for missing GitHub token")


if __name__ == '__main__':
    unittest.main()