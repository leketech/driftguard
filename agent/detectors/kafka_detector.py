#!/usr/bin/env python3
"""
Kafka Detector for DriftGuard
"""

import logging
from typing import Dict, Any, List
from confluent_kafka.admin import AdminClient, ConfigResource
from confluent_kafka import Consumer, KafkaException

logger = logging.getLogger(__name__)

class KafkaDetector:
    """Detector for Kafka resources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.kafka_config = config.get('kafka', {})
        
        # Check if Kafka is configured
        self.kafka_enabled = bool(self.kafka_config.get('bootstrap_servers'))
        
        if self.kafka_enabled:
            self.bootstrap_servers = self.kafka_config.get('bootstrap_servers', 'localhost:9092')
            
            # Prepare Kafka client configuration
            self.client_config = {
                'bootstrap.servers': self.bootstrap_servers,
            }
            
            # Add security configuration if provided
            security_protocol = self.kafka_config.get('security_protocol', 'PLAINTEXT')
            if security_protocol.upper() != 'PLAINTEXT':
                self.client_config['security.protocol'] = security_protocol.lower()
                
                if security_protocol.upper() in ['SASL_SSL', 'SASL_PLAINTEXT']:
                    sasl_mechanism = self.kafka_config.get('sasl_mechanism', '').upper()
                    if sasl_mechanism:
                        self.client_config['sasl.mechanism'] = sasl_mechanism
                        self.client_config['sasl.username'] = self.kafka_config.get('sasl_username', '')
                        self.client_config['sasl.password'] = self.kafka_config.get('sasl_password', '')
                
                ssl_ca_location = self.kafka_config.get('ssl_ca_location', '')
                if ssl_ca_location:
                    self.client_config['ssl.ca.location'] = ssl_ca_location
                    
                ssl_cert_location = self.kafka_config.get('ssl_certificate_location', '')
                if ssl_cert_location:
                    self.client_config['ssl.certificate.location'] = ssl_cert_location
                    
                ssl_key_location = self.kafka_config.get('ssl_key_location', '')
                if ssl_key_location:
                    self.client_config['ssl.key.location'] = ssl_key_location

            try:
                self.admin_client = AdminClient(self.client_config)
            except Exception as e:
                logger.warning(f"Failed to create Kafka admin client: {e}. Kafka functionality disabled.")
                self.kafka_enabled = False
        else:
            logger.info("Kafka not configured, disabling Kafka functionality")
            self.kafka_enabled = False

    def get_desired_state(self) -> Dict[str, Any]:
        """
        Get desired Kafka state from infrastructure-as-code (Helm/Terraform)
        
        Returns:
            Dictionary containing the desired Kafka state
        """
        if not self.kafka_enabled:
            logger.info("Kafka not enabled, returning empty state")
            return {
                "topics": [],
                "acls": [],
                "brokers": [],
                "quotas": []
            }
        
        logger.info("Getting desired Kafka state from IaC...")
        
        # This is a simplified example - in reality, you'd parse Kafka configurations from IaC
        # sources like Helm charts or Terraform files that define Kafka topics, ACLs, etc.
        
        # For now, we'll return an empty structure that would be populated from IaC
        desired_state = {
            "topics": [],
            "acls": [],
            "brokers": [],
            "quotas": []
        }
        
        # In a real implementation, this would:
        # 1. Clone the Git repo containing IaC
        # 2. Parse Kafka configurations from Helm charts or Terraform files
        # 3. Extract topic definitions, ACLs, broker configurations, etc.
        
        return desired_state
    
    def get_live_state(self) -> Dict[str, Any]:
        """
        Get live Kafka state from the cluster
        
        Returns:
            Dictionary containing the live Kafka state
        """
        if not self.kafka_enabled:
            logger.info("Kafka not enabled, returning empty state")
            return {
                "topics": [],
                "brokers": [],
                "acls": [],
                "quotas": []
            }
        
        logger.info("Getting live Kafka state from cluster...")
        
        try:
            # Get list of topics
            metadata = self.admin_client.list_topics(timeout=10)
            topics = []
            
            for topic in metadata.topics.values():
                # Get topic configuration
                topic_configs = self.admin_client.describe_configs([ConfigResource(
                    ConfigResource.Type.TOPIC, topic.topic)])
                
                topic_info = {
                    'name': topic.topic,
                    'partitions': len(topic.partitions),
                    'replication_factor': max([len(partition.replicas) for partition in topic.partitions.values()], default=1),
                    'config': {}
                }
                
                # Extract configuration properties
                for config_resource, config_result in topic_configs.items():
                    try:
                        config_entries = config_result.result()
                        for config_name, config_value in config_entries.items():
                            topic_info['config'][config_name] = config_value.value
                    except Exception as e:
                        logger.warning(f"Could not get config for topic {topic.topic}: {e}")
                
                topics.append(topic_info)
            
            # Get broker information
            brokers = []
            for broker in metadata.brokers.values():
                broker_info = {
                    'id': broker.id,
                    'host': broker.host,
                    'port': broker.port,
                    'rack': broker.rack
                }
                brokers.append(broker_info)
            
            # Build live state
            live_state = {
                "topics": topics,
                "brokers": brokers,
                "acls": [],  # ACLs would be retrieved separately
                "quotas": []  # Quotas would be retrieved separately
            }
            
            logger.info(f"Discovered {len(topics)} topics and {len(brokers)} brokers")
            return live_state
            
        except Exception as e:
            logger.error(f"Error getting live Kafka state: {e}")
            # Return empty state in case of error
            return {
                "topics": [],
                "brokers": [],
                "acls": [],
                "quotas": []
            }