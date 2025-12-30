#!/usr/bin/env python3
"""
Security scanning script for DriftGuard
Performs basic security checks on the codebase
"""

import os
import sys
import subprocess
import json
from typing import List, Dict, Any


def check_hardcoded_credentials(file_path: str) -> List[Dict[str, Any]]:
    """
    Check a file for potential hardcoded credentials
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        List of potential security issues found
    """
    issues = []
    
    # Common patterns that might indicate hardcoded credentials
    credential_patterns = [
        'password',
        'secret',
        'token',
        'key',
        'credential',
        'access_key',
        'secret_key',
        'api_key',
        'auth_token',
        'oauth_token'
    ]
    
    sensitive_prefixes = [
        'AKIA',  # AWS access keys
        'ASIA',  # AWS temporary access keys
    ]
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()
        
        # Check for credential patterns
        for pattern in credential_patterns:
            if pattern in line_lower and '=' in line and not line_lower.strip().startswith('#'):
                # Skip if it's just a variable name or function parameter
                if not any(skip in line_lower for skip in ['def ', 'class ', 'import ', 'from ', '#']):
                    issues.append({
                        'file': file_path,
                        'line': line_num,
                        'code': line.strip(),
                        'issue': f'Potential hardcoded credential containing "{pattern}"',
                        'severity': 'medium'
                    })
        
        # Check for AWS key patterns
        for prefix in sensitive_prefixes:
            if prefix in line and len(line.split(prefix)[1]) >= 16:  # AWS keys are typically 20 chars
                issues.append({
                    'file': file_path,
                    'line': line_num,
                    'code': line.strip(),
                    'issue': f'Potential AWS key starting with "{prefix}"',
                    'severity': 'high'
                })
    
    return issues


def scan_directory(directory: str) -> List[Dict[str, Any]]:
    """
    Scan a directory for security issues
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of security issues found
    """
    issues = []
    
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ['.git', '__pycache__', 'venv', '.venv']):
            continue
            
        for file in files:
            if file.endswith(('.py', '.yaml', '.yml', '.json', '.toml', '.ini', '.cfg', '.conf')):
                file_path = os.path.join(root, file)
                try:
                    file_issues = check_hardcoded_credentials(file_path)
                    issues.extend(file_issues)
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")
    
    return issues


def run_bandit_scan(directory: str) -> List[Dict[str, Any]]:
    """
    Run bandit security scanner if available
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of security issues found by bandit
    """
    try:
        result = subprocess.run([
            sys.executable, '-m', 'bandit',
            '-r', directory,
            '-f', 'json',
            '-ll'  # Medium+ severity
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0 or result.returncode == 1:  # 1 means issues found
            try:
                bandit_output = json.loads(result.stdout)
                issues = []
                
                for result in bandit_output.get('results', []):
                    issues.append({
                        'file': result['filename'],
                        'line': result['line_number'],
                        'code': result['code'],
                        'issue': result['issue_text'],
                        'severity': result['issue_severity'].lower(),
                        'test_id': result['test_id']
                    })
                
                return issues
            except json.JSONDecodeError:
                print("Could not parse bandit output")
                return []
        else:
            print(f"Bandit scan failed: {result.stderr}")
            return []
    except subprocess.TimeoutExpired:
        print("Bandit scan timed out")
        return []
    except FileNotFoundError:
        print("Bandit is not installed. Install with: pip install bandit")
        return []
    except Exception as e:
        print(f"Error running bandit: {e}")
        return []


def run_safety_check() -> List[Dict[str, Any]]:
    """
    Run safety check on requirements if available
    
    Returns:
        List of dependency vulnerabilities
    """
    try:
        result = subprocess.run([
            sys.executable, '-m', 'safety', 'check', '-r', 'requirements.txt', '--json'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 or result.returncode == 1:  # 1 means vulnerabilities found
            try:
                safety_output = json.loads(result.stdout)
                issues = []
                
                for vuln in safety_output:
                    issues.append({
                        'package': vuln['package_name'],
                        'version': vuln['analyzed_version'],
                        'vulnerability': vuln['vulnerability_id'],
                        'description': vuln['description'],
                        'severity': 'high' if vuln['advisory'].startswith('CRITICAL') else 'medium'
                    })
                
                return issues
            except json.JSONDecodeError:
                print("Could not parse safety output")
                return []
        else:
            print(f"Safety check failed: {result.stderr}")
            return []
    except subprocess.TimeoutExpired:
        print("Safety check timed out")
        return []
    except FileNotFoundError:
        print("Safety is not installed. Install with: pip install safety")
        return []
    except Exception as e:
        print(f"Error running safety: {e}")
        return []


def main():
    """Main function to run security scans"""
    print("Running security scans on DriftGuard...")
    
    # Scan the agent directory
    agent_dir = os.path.join(os.path.dirname(__file__), '..', 'agent')
    
    if not os.path.exists(agent_dir):
        print(f"Directory {agent_dir} does not exist")
        return 1
    
    print("Scanning for hardcoded credentials...")
    credential_issues = scan_directory(agent_dir)
    
    print("Running Bandit security scan...")
    bandit_issues = run_bandit_scan(agent_dir)
    
    print("Checking dependencies for vulnerabilities...")
    safety_issues = run_safety_check()
    
    # Combine all issues
    all_issues = {
        'credential_issues': credential_issues,
        'bandit_issues': bandit_issues,
        'safety_issues': safety_issues
    }
    
    # Print summary
    print("\n" + "="*50)
    print("SECURITY SCAN RESULTS")
    print("="*50)
    
    total_issues = 0
    
    if credential_issues:
        print(f"\nHardcoded credential issues found: {len(credential_issues)}")
        for issue in credential_issues:
            print(f"  - {issue['file']}:{issue['line']} - {issue['issue']}")
        total_issues += len(credential_issues)
    
    if bandit_issues:
        print(f"\nBandit issues found: {len(bandit_issues)}")
        for issue in bandit_issues:
            print(f"  - {issue['file']}:{issue['line']} - {issue['issue'][:100]}...")
        total_issues += len(bandit_issues)
    
    if safety_issues:
        print(f"\nDependency vulnerabilities found: {len(safety_issues)}")
        for issue in safety_issues:
            print(f"  - {issue['package']}=={issue['version']} - {issue['description'][:100]}...")
        total_issues += len(safety_issues)
    
    if total_issues == 0:
        print("\nNo security issues found! ✅")
    else:
        print(f"\nTotal security issues found: {total_issues}")
        print("Please address these issues before production deployment.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())