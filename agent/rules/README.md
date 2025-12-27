# DriftGuard Custom Rules

This directory contains custom rules that extend DriftGuard's built-in policy engine.

## Overview

DriftGuard supports extending its policy engine with custom rules. This allows you to:

1. Implement organization-specific security policies
2. Add custom logic for drift classification
3. Define additional ignore patterns
4. Create specialized remediation strategies

## How to Add Custom Rules

1. Create a new Python file in this directory (e.g., `my_rules.py`)
2. Implement functions that match the expected signatures
3. Register your rules in the main policy engine

## Example

See `custom.py` for example implementations of:

- Custom drift severity evaluation
- Custom ignore patterns

## Best Practices

1. Keep rules simple and focused
2. Document your custom rules clearly
3. Test custom rules thoroughly
4. Follow the existing code style and patterns