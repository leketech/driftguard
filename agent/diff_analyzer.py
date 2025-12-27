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
        
        # This is a simplified implementation
        # In reality, you'd have complex logic to compare the states
        diffs = []
        
        # Example diff creation (simplified)
        # In a real implementation, you'd iterate through resources and compare fields
        # For now, only generate a report if we haven't seen any reports for this type of check
        
        # Generate a deterministic drift_id based on the drift characteristics
        # Use a more unique identifier based on what type of check this is
        drift_identifier = f"{desired_state.get('resource_type', 'unknown')}|{desired_state.get('resource_id', 'unknown')}|example.field.path|expected_value|actual_value|{desired_state.get('check_type', 'aws')}"
        drift_id = hashlib.sha256(drift_identifier.encode()).hexdigest()[:16]  # Use first 16 chars
        
        # Check if this drift has already been reported to avoid duplicates
        if drift_id not in self.seen_drifts:
            diff = DriftReport(
                drift_id=drift_id,
                resource_type="example_resource",
                resource_id="example_id",
                drift_type=DriftType.AWS,  # This will be set dynamically in a real implementation
                field_path="example.field.path",
                expected_value="expected_value",
                actual_value="actual_value",
                severity=DriftSeverity.WARNING,
                timestamp="2023-01-01T00:00:00Z"
            )
            diffs.append(diff)
            self.seen_drifts.add(drift_id)
            logger.info(f"New drift detected with ID: {drift_id}")
        else:
            logger.info(f"Duplicate drift detected with ID: {drift_id}, skipping")
        
        return diffs