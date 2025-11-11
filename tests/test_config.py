"""Tests for configuration management."""

import pytest
import tempfile
import yaml
from pathlib import Path

from cloud_automation.config import ConfigManager


def test_config_manager_initialization():
    """Test ConfigManager initialization."""
    manager = ConfigManager()
    assert manager.config == {}


def test_load_config_from_file():
    """Test loading configuration from YAML file."""
    # Create a temporary config file
    config_data = {
        'aws': {
            'region': 'us-west-2',
            'vms': [{'name': 'test-vm'}]
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    try:
        manager = ConfigManager(temp_path)
        assert manager.config == config_data
        assert manager.get('aws.region') == 'us-west-2'
    finally:
        Path(temp_path).unlink()


def test_get_nested_config():
    """Test getting nested configuration values."""
    manager = ConfigManager()
    manager.config = {
        'aws': {
            'region': 'us-east-1',
            'nested': {
                'deep': {
                    'value': 'test'
                }
            }
        }
    }

    assert manager.get('aws.region') == 'us-east-1'
    assert manager.get('aws.nested.deep.value') == 'test'
    assert manager.get('aws.nonexistent', 'default') == 'default'


def test_get_aws_config():
    """Test getting AWS-specific configuration."""
    manager = ConfigManager()
    manager.config = {'aws': {'region': 'us-east-1'}}

    aws_config = manager.get_aws_config()
    assert aws_config == {'region': 'us-east-1'}


def test_get_gcp_config():
    """Test getting GCP-specific configuration."""
    manager = ConfigManager()
    manager.config = {'gcp': {'project_id': 'test-project'}}

    gcp_config = manager.get_gcp_config()
    assert gcp_config == {'project_id': 'test-project'}


def test_load_nonexistent_file():
    """Test loading a nonexistent config file raises error."""
    with pytest.raises(FileNotFoundError):
        ConfigManager('/nonexistent/file.yaml')


def test_validate_aws_config_missing():
    """Test validation fails when AWS config is missing."""
    manager = ConfigManager()
    with pytest.raises(ValueError):
        manager.validate_aws_config()


def test_validate_aws_config_missing_required_field():
    """Test validation fails when required AWS field is missing."""
    manager = ConfigManager()
    manager.config = {'aws': {}}  # Missing 'region'

    with pytest.raises(ValueError):
        manager.validate_aws_config()


def test_validate_gcp_config_missing():
    """Test validation fails when GCP config is missing."""
    manager = ConfigManager()
    with pytest.raises(ValueError):
        manager.validate_gcp_config()


def test_validate_gcp_config_missing_required_field():
    """Test validation fails when required GCP field is missing."""
    manager = ConfigManager()
    manager.config = {'gcp': {}}  # Missing 'project_id'

    with pytest.raises(ValueError):
        manager.validate_gcp_config()
