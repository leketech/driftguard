#!/usr/bin/env python3
"""
Unit tests for DriftGuard configuration loader
"""

import unittest
import os
import tempfile
from unittest.mock import patch, mock_open
from agent.config_loader import load_config

class TestConfigLoader(unittest.TestCase):
    """Test cases for configuration loading"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = """
git:
  repo_url: "https://github.com/test/repo.git"
  branch: "main"
aws:
  region: "us-east-1"
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
"""

    @patch("builtins.open", new_callable=mock_open, read_data="""
git:
  repo_url: "https://github.com/test/repo.git"
  branch: "main"
aws:
  region: "us-east-1"
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
""")
    @patch.dict(os.environ, {
        "GIT_REPO_URL": "https://github.com/env/repo.git",
        "GIT_BRANCH": "develop",
        "AWS_REGION": "us-west-2",
        "TERRAFORM_STATE_KEY": "terraform/env-state.tfstate",
        "GITHUB_TOKEN": "env-token"
    })
    def test_load_config_with_env_override(self, mock_file):
        """Test loading configuration with environment variable overrides"""
        config = load_config("config/config.yaml")
        
        # Environment variables should override config file values
        self.assertEqual(config['git']['repo_url'], "https://github.com/env/repo.git")
        self.assertEqual(config['git']['branch'], "develop")
        self.assertEqual(config['aws']['region'], "us-west-2")
        self.assertEqual(config['aws']['terraform_state_key'], "terraform/env-state.tfstate")
        self.assertEqual(config['github']['token'], "env-token")
        
        # Values not set in env should remain from config file
        self.assertEqual(config['logging']['level'], "INFO")
        self.assertEqual(config['output']['format'], "json")

    @patch("builtins.open", new_callable=mock_open, read_data="""
git:
  repo_url: "https://github.com/test/repo.git"
  branch: "main"
aws:
  region: "us-east-1"
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
""")
    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_without_env(self, mock_file):
        """Test loading configuration without environment variables"""
        config = load_config("config/config.yaml")
        
        # Should use values from config file
        self.assertEqual(config['git']['repo_url'], "https://github.com/test/repo.git")
        self.assertEqual(config['git']['branch'], "main")
        self.assertEqual(config['aws']['region'], "us-east-1")
        self.assertEqual(config['aws']['terraform_state_key'], "terraform/state.tfstate")
        self.assertEqual(config['github']['token'], "test-token")

if __name__ == '__main__':
    unittest.main()