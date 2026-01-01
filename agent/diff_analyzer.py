#!/usr/bin/env python3
"""
Diff Analyzer for DriftGuard
"""

import logging
import hashlib
from typing import Dict, Any, List
from models import DriftReport, DriftType, DriftSeverity

logger = logging.getLogger(__name__)

class DiffAnalyzer:
    """Analyzer for computing differences between desired and live states"""
    
    def __init__(self):
        self.seen_drifts = set()  # Track seen drift IDs to prevent duplicates
    
    def compute_diffs(self, desired_state: Dict[str, Any], live_state: Dict[str, Any]) -> List[DriftReport]:
        """
        Compute differences between desired and live states
        
        Args:
            desired_state: The desired state from IaC
            live_state: The live state from cloud/K8s
            
        Returns:
            List of DriftReport objects
        """
        logger.info("Computing differences between desired and live states...")
        
        diffs = []
        
        try:
            # Compare resources in desired vs live state
            desired_resources = desired_state.get('resources', desired_state.get('deployments', []))
            live_resources = live_state.get('ec2_instances', live_state.get('deployments', []))
            
            # For AWS resources
            if 'resources' in desired_state and 'ec2_instances' in live_state:
                diffs.extend(self._compare_aws_resources(desired_state, live_state))
            # For Kubernetes resources
            elif 'deployments' in desired_state and 'deployments' in live_state:
                diffs.extend(self._compare_k8s_resources(desired_state, live_state))
            # For Kafka resources
            elif 'topics' in desired_state and 'topics' in live_state:
                diffs.extend(self._compare_kafka_resources(desired_state, live_state))
            else:
                # Generic comparison for other resource types
                diffs.extend(self._compare_generic_resources(desired_state, live_state))
                
        except Exception as e:
            logger.error(f"Error computing diffs: {e}", exc_info=True)
            # Return empty list if there's an error, so the system can continue
            return []
        
        # Remove duplicate drift reports
        unique_diffs = []
        seen_ids = set()
        for diff in diffs:
            if diff.drift_id not in seen_ids:
                unique_diffs.append(diff)
                seen_ids.add(diff.drift_id)
        
        logger.info(f"Computed {len(unique_diffs)} unique differences")
        
        return unique_diffs
    
    def _compare_aws_resources(self, desired_state: Dict[str, Any], live_state: Dict[str, Any]) -> List[DriftReport]:
        """Compare AWS resources between desired and live states"""
        diffs = []
        
        # Compare resources
        desired_resources = desired_state.get('resources', [])
        live_ec2_instances = live_state.get('ec2_instances', {})
        live_security_groups = live_state.get('security_groups', {})
        
        # Example: Compare EC2 instances
        # In real implementation, we would compare actual resource values
        for resource in desired_resources:
            resource_type = resource.get('type', '')
            resource_name = resource.get('name', '')
            resource_values = resource.get('values', {})
            
            # Generate drift reports based on differences
            # This is a simplified example - in reality, you'd compare specific fields
            if resource_type == 'aws_instance':
                # Compare specific fields like instance type, tags, etc.
                for field, expected_value in resource_values.items():
                    # In real implementation, compare with live state
                    drift_id = hashlib.sha256(f"aws_{resource_type}_{resource_name}_{field}".encode()).hexdigest()[:16]
                    
                    # For now, just create example drifts
                    if drift_id not in self.seen_drifts:
                        diff = DriftReport(
                            drift_id=drift_id,
                            resource_type=resource_type,
                            resource_id=f"{resource_type}.{resource_name}",
                            drift_type=DriftType.AWS,
                            field_path=field,
                            expected_value=expected_value,
                            actual_value="live_value",  # Would come from live state
                            severity=DriftSeverity.WARNING,
                            timestamp="2023-01-01T00:00:00Z"
                        )
                        diffs.append(diff)
                        self.seen_drifts.add(drift_id)
        
        return diffs
    
    def _compare_k8s_resources(self, desired_state: Dict[str, Any], live_state: Dict[str, Any]) -> List[DriftReport]:
        """Compare Kubernetes resources between desired and live states"""
        diffs = []
        
        # Compare deployments
        desired_deployments = desired_state.get('deployments', [])
        live_deployments = live_state.get('deployments', {})
        
        for desired_deployment in desired_deployments:
            if desired_deployment and isinstance(desired_deployment, dict):
                deployment_name = desired_deployment.get('metadata', {}).get('name', 'unknown')
                deployment_namespace = desired_deployment.get('metadata', {}).get('namespace', 'default')
                
                # Compare deployment spec
                desired_spec = desired_deployment.get('spec', {})
                
                # In real implementation, find corresponding live deployment and compare specs
                for field_path, expected_value in self._flatten_dict(desired_spec).items():
                    drift_id = hashlib.sha256(f"k8s_deployment_{deployment_namespace}_{deployment_name}_{field_path}".encode()).hexdigest()[:16]
                    
                    if drift_id not in self.seen_drifts:
                        diff = DriftReport(
                            drift_id=drift_id,
                            resource_type="k8s_deployment",
                            resource_id=f"{deployment_namespace}/{deployment_name}",
                            drift_type=DriftType.KUBERNETES,
                            field_path=field_path,
                            expected_value=expected_value,
                            actual_value="live_value",  # Would come from live state
                            severity=DriftSeverity.WARNING,
                            timestamp="2023-01-01T00:00:00Z"
                        )
                        diffs.append(diff)
                        self.seen_drifts.add(drift_id)
        
        return diffs
    
    def _compare_kafka_resources(self, desired_state: Dict[str, Any], live_state: Dict[str, Any]) -> List[DriftReport]:
        """Compare Kafka resources between desired and live states"""
        diffs = []
        
        # Compare topics
        desired_topics = desired_state.get('topics', [])
        live_topics = live_state.get('topics', [])
        
        # In real implementation, compare topic configurations
        for desired_topic in desired_topics:
            if isinstance(desired_topic, dict):
                topic_name = desired_topic.get('name', 'unknown')
                
                for field_path, expected_value in self._flatten_dict(desired_topic).items():
                    drift_id = hashlib.sha256(f"kafka_topic_{topic_name}_{field_path}".encode()).hexdigest()[:16]
                    
                    if drift_id not in self.seen_drifts:
                        diff = DriftReport(
                            drift_id=drift_id,
                            resource_type="kafka_topic",
                            resource_id=topic_name,
                            drift_type=DriftType.KAFKA,
                            field_path=field_path,
                            expected_value=expected_value,
                            actual_value="live_value",  # Would come from live state
                            severity=DriftSeverity.WARNING,
                            timestamp="2023-01-01T00:00:00Z"
                        )
                        diffs.append(diff)
                        self.seen_drifts.add(drift_id)
        
        return diffs
    
    def _compare_generic_resources(self, desired_state: Dict[str, Any], live_state: Dict[str, Any]) -> List[DriftReport]:
        """Compare generic resources between desired and live states"""
        diffs = []
        
        # Flatten both desired and live states to compare all fields
        desired_flat = self._flatten_dict(desired_state)
        live_flat = self._flatten_dict(live_state)
        
        # Compare each field in desired state with live state
        for field_path, expected_value in desired_flat.items():
            actual_value = live_flat.get(field_path)
            
            if expected_value != actual_value:
                drift_id = hashlib.sha256(f"generic_{field_path}".encode()).hexdigest()[:16]
                
                if drift_id not in self.seen_drifts:
                    diff = DriftReport(
                        drift_id=drift_id,
                        resource_type="generic",
                        resource_id="unknown",
                        drift_type=DriftType.AWS,  # Default to AWS
                        field_path=field_path,
                        expected_value=expected_value,
                        actual_value=actual_value,
                        severity=DriftSeverity.WARNING,
                        timestamp="2023-01-01T00:00:00Z"
                    )
                    diffs.append(diff)
                    self.seen_drifts.add(drift_id)
        
        return diffs
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary for easier comparison
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested fields
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary with dot notation keys
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)