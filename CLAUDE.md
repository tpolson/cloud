# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based cloud automation framework called "cloud-automation" that provides automated VM and storage provisioning for AWS and Google Cloud platforms. The project is in early development stage (Alpha) and uses a modular architecture with separate AWS and GCP modules.

## Project Structure

```
cloud_automation/
├── aws/           # AWS-specific provisioning modules
├── gcp/           # Google Cloud-specific provisioning modules
└── cli.py         # Main CLI entry point (referenced in setup.py)
configs/           # Configuration files and templates
tests/             # Test suite
```

## Development Setup

### Installation
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt
```

### CLI Usage
The main entry point is available as a console script after installation:
```bash
cloud-provision --help
```

## Common Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_filename.py

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code
black cloud_automation/ tests/

# Lint code
flake8 cloud_automation/ tests/

# Type checking
mypy cloud_automation/
```

### Package Management
```bash
# Install package in development mode
pip install -e .

# Build distribution
python setup.py sdist bdist_wheel
```

## Architecture Notes

- **Multi-cloud support**: Separate modules for AWS (boto3) and GCP (google-cloud-*)
- **CLI framework**: Uses Click for command-line interface
- **Configuration**: YAML-based configuration with Jinja2 templating support
- **Python compatibility**: Supports Python 3.8+
- **Entry point**: Main CLI accessible via `cloud-provision` command

## Cloud Provider Integration

### AWS Integration
- Uses boto3/botocore for AWS API interactions
- AWS-specific code should go in `cloud_automation/aws/`

### Google Cloud Integration
- Uses google-cloud-compute and google-cloud-storage libraries
- GCP-specific code should go in `cloud_automation/gcp/`

## Development Guidelines

- Follow Python 3.8+ compatibility requirements
- Use type hints (mypy enforcement)
- Maintain separation between AWS and GCP implementations
- Configuration files should use YAML format
- CLI commands should use Click decorators