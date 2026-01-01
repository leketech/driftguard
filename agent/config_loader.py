#!/usr/bin/env python3
"""
Configuration Loader for DriftGuard
"""

import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file and environment variables
    
    Args:
        config_path: Path to the configuration file. If None, uses default location.
        
    Returns:
        Dictionary containing the configuration
    """
    if config_path is None:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Config is at driftguard/config/config.yaml (one level up from agent/)
        config_path = os.path.join(script_dir, '..', 'config', 'config.yaml')
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
    
    # Validate configuration
    validate_config(config)
    
    return config

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the loaded configuration
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    errors = []
    
    # Validate Git configuration
    git_config = config.get('git', {})
    if not git_config.get('repo_url'):
        errors.append("Git repository URL is required")
    elif not isinstance(git_config['repo_url'], str) or not git_config['repo_url'].strip():
        errors.append("Git repository URL must be a non-empty string")
    
    if not git_config.get('branch'):
        errors.append("Git branch is required")
    elif not isinstance(git_config['branch'], str) or not git_config['branch'].strip():
        errors.append("Git branch must be a non-empty string")
    
    # Validate AWS configuration
    aws_config = config.get('aws', {})
    if not aws_config.get('region'):
        errors.append("AWS region is required")
    elif not isinstance(aws_config['region'], str) or not aws_config['region'].strip():
        errors.append("AWS region must be a non-empty string")
    
    if not aws_config.get('account_id'):
        errors.append("AWS account ID is required")
    elif not isinstance(aws_config['account_id'], str) or not aws_config['account_id'].strip():
        errors.append("AWS account ID must be a non-empty string")
    
    if not aws_config.get('terraform_state_key'):
        errors.append("Terraform state key is required")
    elif not isinstance(aws_config['terraform_state_key'], str) or not aws_config['terraform_state_key'].strip():
        errors.append("Terraform state key must be a non-empty string")
    
    # Validate GitHub configuration
    github_config = config.get('github', {})
    if not github_config.get('token'):
        logger.warning("GitHub token is not set. Some features may not work properly.")
    elif not isinstance(github_config['token'], str) or not github_config['token'].strip():
        errors.append("GitHub token must be a non-empty string if provided")
    
    # Validate Kafka configuration if provided
    kafka_config = config.get('kafka', {})
    if kafka_config.get('bootstrap_servers'):
        if not isinstance(kafka_config['bootstrap_servers'], str) or not kafka_config['bootstrap_servers'].strip():
            errors.append("Kafka bootstrap servers must be a non-empty string if provided")
    
    # Validate output configuration
    output_config = config.get('output', {})
    destination = output_config.get('destination', 'stdout')
    if destination not in ['stdout', 's3', 'file']:
        errors.append(f"Output destination '{destination}' is not valid. Must be one of: stdout, s3, file")
    
    # Validate logging configuration
    logging_config = config.get('logging', {})
    log_level = logging_config.get('level', 'INFO')
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        errors.append(f"Log level '{log_level}' is not valid. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    
    if errors:
        error_msg = "Configuration validation failed with the following errors:\n" + "\n".join([f"  - {error}" for error in errors])
        logger.error(error_msg)
        raise ValueError(error_msg)