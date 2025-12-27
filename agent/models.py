#!/usr/bin/env python3
"""
Data Models for DriftGuard
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class DriftSeverity(str, Enum):
    """Severity levels for drift detection"""
    SAFE = "safe"
    WARNING = "warning"
    CRITICAL = "critical"
    IGNORED = "ignored"

class DriftType(str, Enum):
    """Types of drift"""
    AWS = "aws"
    KUBERNETES = "kubernetes"
    KAFKA = "kafka"

class DriftReport(BaseModel):
    """Model for drift detection reports"""
    drift_id: str  # Unique identifier for deduplication
    resource_type: str
    resource_id: str
    drift_type: DriftType
    field_path: str
    expected_value: Any
    actual_value: Any
    severity: DriftSeverity
    timestamp: str

class RemediationAction(BaseModel):
    """Model for remediation actions"""
    action_type: str
    resource_type: str
    resource_id: str
    description: str
    auto_apply: bool
    timestamp: str

class Config(BaseModel):
    """Main configuration model"""
    git: Dict[str, str]
    aws: Dict[str, str]
    github: Dict[str, str]
    logging: Dict[str, str]
    output: Dict[str, str]