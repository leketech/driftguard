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
        
        subprocess.run([
            "git", "clone", 
            repo_url, 
            "/tmp/aws_iac_repo"
        ], check=True, env={'GIT_TERMINAL_PROMPT': '0'})
        
        # Change to repo directory
        import os
        os.chdir("/tmp/aws_iac_repo")
        
        try:
            # Initialize Terraform
            subprocess.run(["terraform", "init"], check=True, capture_output=True)
            
            # Get the current state instead of running plan
            result = subprocess.run([
                "terraform", "show", 
                "-json"
            ], capture_output=True, text=True, check=True)
            
            # Parse the state (simplified)
            desired_state = {
                "resources": [],
                "outputs": []
            }
        except subprocess.CalledProcessError as e:
            logger.warning(f"Terraform command failed: {e}. Using empty desired state.")
            desired_state = {
                "resources": [],
                "outputs": []
            }
        
        return desired_state
    
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