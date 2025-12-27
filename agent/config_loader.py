#!/usr/bin/env python3
"""
Configuration Loader for DriftGuard
"""

import os
import yaml
from typing import Dict, Any

def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration
    """
    # Load config from YAML file
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Override with environment variables
    config['git']['repo_url'] = os.getenv('GIT_REPO_URL', config['git']['repo_url'])
    config['git']['branch'] = os.getenv('GIT_BRANCH', config['git']['branch'])
    config['aws']['region'] = os.getenv('AWS_REGION', config['aws']['region'])
    config['aws']['account_id'] = os.getenv('AWS_ACCOUNT_ID', config['aws']['account_id'])
    config['aws']['terraform_state_key'] = os.getenv('TERRAFORM_STATE_KEY', config['aws']['terraform_state_key'])
    config['github']['token'] = os.getenv('GITHUB_TOKEN', config['github']['token'])
    
    # Kafka configuration
    # Initialize Kafka config if it doesn't exist
    if 'kafka' not in config:
        config['kafka'] = {}
    
    config['kafka']['bootstrap_servers'] = os.getenv('KAFKA_BOOTSTRAP_SERVERS', config['kafka'].get('bootstrap_servers', 'localhost:9092'))
    config['kafka']['security_protocol'] = os.getenv('KAFKA_SECURITY_PROTOCOL', config['kafka'].get('security_protocol', 'PLAINTEXT'))
    config['kafka']['sasl_mechanism'] = os.getenv('KAFKA_SASL_MECHANISM', config['kafka'].get('sasl_mechanism'))
    config['kafka']['sasl_username'] = os.getenv('KAFKA_SASL_USERNAME', config['kafka'].get('sasl_username'))
    config['kafka']['sasl_password'] = os.getenv('KAFKA_SASL_PASSWORD', config['kafka'].get('sasl_password'))
    config['kafka']['ssl_ca_location'] = os.getenv('KAFKA_SSL_CA_LOCATION', config['kafka'].get('ssl_ca_location'))
    config['kafka']['ssl_certificate_location'] = os.getenv('KAFKA_SSL_CERTIFICATE_LOCATION', config['kafka'].get('ssl_certificate_location'))
    config['kafka']['ssl_key_location'] = os.getenv('KAFKA_SSL_KEY_LOCATION', config['kafka'].get('ssl_key_location'))
    config['kafka']['consumer_group'] = os.getenv('KAFKA_CONSUMER_GROUP', config['kafka'].get('consumer_group', 'driftguard-consumer-group'))
    
    return config