# DriftGuard Tests

This directory contains unit tests for the DriftGuard project.

## Running Tests

### Using the Test Runner Script

```bash
python tests/run_tests.py
```

### Using Python's unittest module directly

```bash
python -m unittest discover tests
```

### Running Individual Test Files

```bash
python -m unittest tests.test_models
python -m unittest tests.test_config_loader
python -m unittest tests.test_policy_engine
```

## Test Organization

- `test_models.py` - Tests for data models
- `test_config_loader.py` - Tests for configuration loading
- `test_policy_engine.py` - Tests for policy engine logic
- `run_tests.py` - Test runner script

## Adding New Tests

1. Create a new test file with the naming pattern `test_*.py`
2. Import the necessary modules and create test classes that inherit from `unittest.TestCase`
3. Add test methods that start with `test_`
4. Run the tests to ensure they pass

## Test Coverage

The tests cover:
- Data model validation
- Configuration loading and environment variable overriding
- Policy engine logic for drift classification
- Basic functionality of core components