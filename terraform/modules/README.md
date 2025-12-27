# DriftGuard Terraform Modules

This directory contains reusable Terraform modules for DriftGuard.

## Module Structure

```
modules/
├── iam-policy/          # Shared IAM policy module
└── (future modules)
```

## Shared Modules

### iam-policy

The `iam-policy` module provides a reusable IAM policy definition that is consumed by other modules. This ensures consistent permissions across all DriftGuard components.

By centralizing the policy definition, we eliminate duplication and ensure that any updates to the required permissions are automatically propagated to all modules that use this policy.

## Usage

Modules in this directory are consumed by the top-level modules in the parent directory:

- `../iam` - The main IAM module for DriftGuard agent
- `../oidc` - The OIDC module for GitHub Actions integration

This structure promotes reusability and maintainability by following the DRY (Don't Repeat Yourself) principle.