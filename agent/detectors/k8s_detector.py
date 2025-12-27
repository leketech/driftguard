#!/usr/bin/env python3
"""
Kubernetes Detector for DriftGuard
"""

import subprocess
import yaml
import json
import logging
from typing import Dict, Any
from kubernetes import client
from kubernetes import config as k8s_config

logger = logging.getLogger(__name__)

class K8sDetector:
    """Detector for Kubernetes resources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        try:
            # Try to load in-cluster config first
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            # Fall back to kubeconfig
            try:
                k8s_config.load_kube_config()
            except FileNotFoundError:
                # If no kubeconfig, set up dummy config
                logger.warning("No Kubernetes configuration found. Using dummy config.")
        
    def get_desired_state(self) -> Dict[str, Any]:
        """
        Get desired Kubernetes state from Helm templates
        
        Returns:
            Dictionary containing the desired Kubernetes state
        """
        logger.info("Getting desired Kubernetes state from Helm...")
        
        # Clone the Git repo to a different directory
        subprocess.run([
            "git", "clone", 
            self.config['git']['repo_url'], 
            "/tmp/k8s_iac_repo"
        ], check=True)
        
        # Change to repo directory
        import os
        os.chdir("/tmp/k8s_iac_repo")
        
        # Check if there are any Helm charts in the repo
        import os
        helm_chart_dirs = []
        for root, dirs, files in os.walk("."):
            if "Chart.yaml" in files:
                helm_chart_dirs.append(root)
        
        if not helm_chart_dirs:
            logger.info("No Helm charts found in the repository")
            # Parse the templates (simplified)
            desired_state = {
                "deployments": [],
                "services": [],
                "configmaps": []
            }
            return desired_state
        
        # Run helm template for each chart found
        for chart_dir in helm_chart_dirs:
            chart_name = os.path.basename(chart_dir)
            output_dir = f"/tmp/helm_templates_{chart_name}"
            os.makedirs(output_dir, exist_ok=True)
            
            result = subprocess.run([
                "helm", "template", 
                chart_name,
                chart_dir,
                "--output-dir", output_dir
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"Helm template failed for chart {chart_dir}: {result.stderr}")
            else:
                logger.info(f"Successfully processed Helm chart {chart_dir}")
        
        # Parse the templates (simplified)
        desired_state = {
            "deployments": [],
            "services": [],
            "configmaps": []
        }
        
        return desired_state
        
        # Parse the templates (simplified)
        desired_state = {
            "deployments": [],
            "services": [],
            "configmaps": []
        }
        
        return desired_state
    
    def get_live_state(self) -> Dict[str, Any]:
        """
        Get live Kubernetes state from the cluster
        
        Returns:
            Dictionary containing the live Kubernetes state
        """
        logger.info("Getting live Kubernetes state from cluster...")
        
        # Initialize Kubernetes clients
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        
        # Get namespaces
        namespaces = v1.list_namespace()
        
        # Get deployments
        deployments = apps_v1.list_deployment_for_all_namespaces()
        
        # Get services
        services = v1.list_service_for_all_namespaces()
        
        # Get configmaps
        configmaps = v1.list_config_map_for_all_namespaces()
        
        # Build live state
        live_state = {
            "namespaces": namespaces,
            "deployments": deployments,
            "services": services,
            "configmaps": configmaps
        }
        
        return live_state