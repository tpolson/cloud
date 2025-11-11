"""Tests for utility functions."""

import pytest
from cloud_automation.utils import (
    format_tags,
    format_labels,
    validate_name,
    parse_size,
)


def test_format_tags():
    """Test AWS tag formatting."""
    tags = {'Environment': 'production', 'Team': 'DevOps'}
    formatted = format_tags(tags)

    assert len(formatted) == 2
    assert {'Key': 'Environment', 'Value': 'production'} in formatted
    assert {'Key': 'Team', 'Value': 'DevOps'} in formatted


def test_format_labels():
    """Test GCP label formatting."""
    labels = {'Environment': 'Production', 'Team_Name': 'DevOps'}
    formatted = format_labels(labels)

    # GCP labels should be lowercase with hyphens
    assert formatted == {'environment': 'production', 'team-name': 'devops'}


def test_validate_name_aws():
    """Test AWS name validation."""
    assert validate_name('valid-name', 'aws') is True
    assert validate_name('valid_name', 'aws') is True
    assert validate_name('ValidName123', 'aws') is True

    with pytest.raises(ValueError):
        validate_name('', 'aws')

    with pytest.raises(ValueError):
        validate_name('a' * 300, 'aws')  # Too long


def test_validate_name_gcp():
    """Test GCP name validation."""
    assert validate_name('valid-name', 'gcp') is True
    assert validate_name('valid-name-123', 'gcp') is True

    # Must start with letter
    with pytest.raises(ValueError):
        validate_name('123-invalid', 'gcp')

    # Must be lowercase
    with pytest.raises(ValueError):
        validate_name('Invalid-Name', 'gcp')

    # Must end with letter or number
    with pytest.raises(ValueError):
        validate_name('invalid-', 'gcp')

    # Too long
    with pytest.raises(ValueError):
        validate_name('a' * 100, 'gcp')

    # Empty name
    with pytest.raises(ValueError):
        validate_name('', 'gcp')


def test_parse_size():
    """Test storage size parsing."""
    assert parse_size('100') == 100
    assert parse_size('100GB') == 100
    assert parse_size('1TB') == 1024
    assert parse_size('2TB') == 2048
    assert parse_size('512') == 512

    with pytest.raises(ValueError):
        parse_size('invalid')

    with pytest.raises(ValueError):
        parse_size('100MB')  # Not supported


def test_parse_size_case_insensitive():
    """Test size parsing is case insensitive."""
    assert parse_size('100gb') == 100
    assert parse_size('1tb') == 1024
    assert parse_size('100GB') == 100
    assert parse_size('1TB') == 1024
