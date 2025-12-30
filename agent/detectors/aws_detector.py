#!/usr/bin/env python3
"""
AWS Detector for DriftGuard
"""

import boto3
import subprocess
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AWSDetector:
    """Detector for AWS resources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.aws_region = config['aws']['region']
        self.aws_account_id = config['aws'].get('account_id', '')
        self.terraform_state_key = config['aws']['terraform_state_key']
        
    def get_desired_state(self) -> Dict[str, Any]:
        """
        Get desired AWS state from Terraform state
        
        Returns:
            Dictionary containing the desired AWS state
        """
        logger.info("Getting desired AWS state from Terraform...")
        
        # Clone the Git repo to a different directory
        repo_url = self.config['git']['repo_url']
        
        # Use GitHub token for authentication if provided
        github_token = self.config.get('github', {}).get('token', '')
        if github_token and github_token != 'dummy-token-for-now':
            # Replace https:// with https://token@ for authentication
            if repo_url.startswith('https://github.com/'):
                repo_url = repo_url.replace('https://github.com/', f'https://{github_token}@github.com/')
        
        # Use platform-appropriate temp directory
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp(prefix="driftguard_aws_")
        repo_path = os.path.join(temp_dir, "aws_iac_repo")
        
        subprocess.run([
            "git", "clone", 
            repo_url, 
            repo_path
        ], check=True, env={'GIT_TERMINAL_PROMPT': '0'})
        
        # Change to repo directory
        os.chdir(repo_path)
        
        try:
            # Initialize Terraform
            subprocess.run(["terraform", "init"], check=True, capture_output=True)
            
            # Get the current state instead of running plan
            result = subprocess.run([
                "terraform", "show", 
                "-json"
            ], capture_output=True, text=True, check=True)
            
            # Parse the Terraform state JSON
            terraform_state = json.loads(result.stdout)
            desired_state = self._parse_terraform_state(terraform_state)
        except subprocess.CalledProcessError as e:
            logger.error(f"Terraform command failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Terraform state JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing Terraform state: {e}")
            raise
        
        return desired_state
    
    def _parse_terraform_state(self, terraform_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Terraform state JSON to extract resource information
        
        Args:
            terraform_state: Raw Terraform state JSON
            
        Returns:
            Dictionary containing parsed resources and outputs
        """
        resources = []
        
        # Extract resources from state
        if 'values' in terraform_state:
            state_values = terraform_state['values']
            
            # Process resources
            if 'root_module' in state_values:
                root_module = state_values['root_module']
                
                # Process resources in the root module
                if 'resources' in root_module:
                    for resource in root_module['resources']:
                        resource_info = {
                            'type': resource.get('type', ''),
                            'name': resource.get('name', ''),
                            'provider': resource.get('provider_name', ''),
                            'values': resource.get('values', {}),
                            'address': resource.get('address', ''),
                            'mode': resource.get('mode', '')
                        }
                        resources.append(resource_info)
                
                # Process child modules if they exist
                if 'child_modules' in root_module:
                    for module in root_module['child_modules']:
                        if 'resources' in module:
                            for resource in module['resources']:
                                resource_info = {
                                    'type': resource.get('type', ''),
                                    'name': resource.get('name', ''),
                                    'provider': resource.get('provider_name', ''),
                                    'values': resource.get('values', {}),
                                    'address': resource.get('address', ''),
                                    'mode': resource.get('mode', '')
                                }
                                resources.append(resource_info)
        
        # Extract outputs
        outputs = {}
        if 'values' in terraform_state:
            state_values = terraform_state['values']
            if 'outputs' in state_values:
                for output_name, output_value in state_values['outputs'].items():
                    outputs[output_name] = output_value.get('value', None)
        
        return {
            "resources": resources,
            "outputs": outputs
        }
    
    def get_live_state(self) -> Dict[str, Any]:
        """
        Get live AWS state from AWS APIs
        
        Returns:
            Dictionary containing the live AWS state
        """
        logger.info("Getting live AWS state from APIs...")
        
        # Initialize AWS clients
        ec2 = boto3.client('ec2', region_name=self.aws_region)
        s3 = boto3.client('s3', region_name=self.aws_region)
        
        # Get EC2 instances
        ec2_instances = ec2.describe_instances()
        
        # Get security groups
        security_groups = ec2.describe_security_groups()
        
        # Build live state
        live_state = {
            "ec2_instances": ec2_instances,
            "security_groups": security_groups
        }
        
        return live_state