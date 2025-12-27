# DriftGuard Runtime Outputs

This directory is used for runtime-generated files such as:
- Drift reports
- Log files
- Temporary files

## Important Notes

- This directory is intentionally kept empty in the repository
- Files in this directory are generated during DriftGuard execution
- Files in this directory should NOT be committed to version control
- The `.gitkeep` file ensures this directory exists when cloning the repository

## Generated File Types

During execution, DriftGuard may generate:
- JSON reports
- CSV reports
- Log files
- Temporary state files

## Cleanup

You can safely delete files in this directory to clean up old reports and logs.