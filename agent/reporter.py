#!/usr/bin/env python3
"""
Reporter for DriftGuard
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import boto3
from models import DriftReport, RemediationAction

logger = logging.getLogger(__name__)

class Reporter:
    """Reporter for generating and storing drift reports"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def report(self, drift_reports: List[DriftReport], actions: List[RemediationAction]):
        """
        Generate and store reports
        
        Args:
            drift_reports: List of DriftReport objects
            actions: List of RemediationAction objects
        """
        logger.info("Generating and storing reports...")
        
        # Deduplicate drift reports based on drift_id
        unique_reports = {}
        for report in drift_reports:
            if report.drift_id not in unique_reports:
                unique_reports[report.drift_id] = report
        
        unique_drift_reports = list(unique_reports.values())
        
        # Create report data with all reports in a single array
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "drift_reports": [report.dict() for report in unique_drift_reports],
            "actions": [action.dict() for action in actions]
        }
        
        # Store report based on configuration
        output_dest = self.config['output']['destination']
        
        if output_dest == "stdout":
            self._output_to_stdout(report_data)
        elif output_dest == "s3":
            self._output_to_s3(report_data)
        elif output_dest == "file":
            self._output_to_file(report_data)
    
    def _output_to_stdout(self, report_data: Dict[str, Any]):
        """
        Output report to stdout
        
        Args:
            report_data: Report data to output
        """
        print(json.dumps(report_data, indent=2))
    
    def _output_to_s3(self, report_data: Dict[str, Any]):
        """
        Output report to S3
        
        Args:
            report_data: Report data to output
        """
        s3 = boto3.client('s3')
        bucket = self.config['aws']['s3_bucket']
        key = f"driftguard-reports/{datetime.utcnow().strftime('%Y/%m/%d')}/report.json"
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(report_data),
            ContentType='application/json'
        )
        
        logger.info(f"Report stored to s3://{bucket}/{key}")
    
    def _output_to_file(self, report_data: Dict[str, Any]):
        """
        Output report to file
        
        Args:
            report_data: Report data to output
        """
        filename = f"outputs/report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Report stored to {filename}")