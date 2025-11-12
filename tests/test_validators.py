"""Tests for input validators."""

import pytest
from cloud_automation.validators import AWSValidator, GCPValidator, CommonValidator, ValidationError


class TestAWSValidator:
    """Test AWS input validators."""

    def test_valid_ami_id(self):
        """Test valid AMI ID passes validation."""
        ami_id = "ami-0abcdef1234567890"
        result = AWSValidator.validate_ami_id(ami_id)
        assert result == ami_id

    def test_invalid_ami_id_format(self):
        """Test invalid AMI ID format raises error."""
        with pytest.raises(ValidationError, match="Invalid AMI ID format"):
            AWSValidator.validate_ami_id("ami-invalid")

        with pytest.raises(ValidationError):
            AWSValidator.validate_ami_id("not-an-ami")

    def test_empty_ami_id(self):
        """Test empty AMI ID raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            AWSValidator.validate_ami_id("")

    def test_valid_instance_id(self):
        """Test valid instance ID passes validation."""
        instance_id = "i-1234567890abcdef0"
        result = AWSValidator.validate_instance_id(instance_id)
        assert result == instance_id

    def test_invalid_instance_id(self):
        """Test invalid instance ID raises error."""
        with pytest.raises(ValidationError, match="Invalid Instance ID"):
            AWSValidator.validate_instance_id("instance-123")

    def test_valid_volume_id(self):
        """Test valid volume ID passes validation."""
        volume_id = "vol-049df61146c4d7901"
        result = AWSValidator.validate_volume_id(volume_id)
        assert result == volume_id

    def test_valid_instance_type(self):
        """Test valid instance type passes validation."""
        instance_type = "t2.micro"
        result = AWSValidator.validate_instance_type(instance_type)
        assert result == instance_type

    def test_invalid_instance_type(self):
        """Test invalid instance type raises error."""
        with pytest.raises(ValidationError, match="Unknown AWS instance type"):
            AWSValidator.validate_instance_type("invalid.type")

    def test_valid_region(self):
        """Test valid region passes validation."""
        region = "us-east-1"
        result = AWSValidator.validate_region(region)
        assert result == region

    def test_invalid_region(self):
        """Test invalid region raises error."""
        with pytest.raises(ValidationError, match="Invalid AWS region"):
            AWSValidator.validate_region("invalid-region")

    def test_valid_s3_bucket_name(self):
        """Test valid S3 bucket name passes validation."""
        bucket = "my-test-bucket-123"
        result = AWSValidator.validate_s3_bucket_name(bucket)
        assert result == bucket

    def test_invalid_s3_bucket_too_short(self):
        """Test S3 bucket name too short raises error."""
        with pytest.raises(ValidationError, match="between 3 and 63 characters"):
            AWSValidator.validate_s3_bucket_name("ab")

    def test_invalid_s3_bucket_uppercase(self):
        """Test S3 bucket with uppercase raises error."""
        with pytest.raises(ValidationError):
            AWSValidator.validate_s3_bucket_name("MyBucket")

    def test_invalid_s3_bucket_ip_format(self):
        """Test S3 bucket formatted as IP raises error."""
        with pytest.raises(ValidationError, match="IP address"):
            AWSValidator.validate_s3_bucket_name("192.168.1.1")


class TestGCPValidator:
    """Test GCP input validators."""

    def test_valid_project_id(self):
        """Test valid project ID passes validation."""
        project_id = "my-test-project-123"
        result = GCPValidator.validate_project_id(project_id)
        assert result == project_id

    def test_invalid_project_id_too_short(self):
        """Test project ID too short raises error."""
        with pytest.raises(ValidationError, match="between 6 and 30 characters"):
            GCPValidator.validate_project_id("short")

    def test_invalid_project_id_uppercase(self):
        """Test project ID with uppercase raises error."""
        with pytest.raises(ValidationError):
            GCPValidator.validate_project_id("MyProject")

    def test_valid_instance_name(self):
        """Test valid instance name passes validation."""
        name = "my-instance-1"
        result = GCPValidator.validate_instance_name(name)
        assert result == name

    def test_invalid_instance_name_too_long(self):
        """Test instance name too long raises error."""
        long_name = "a" * 64
        with pytest.raises(ValidationError, match="63 characters or less"):
            GCPValidator.validate_instance_name(long_name)

    def test_invalid_instance_name_uppercase(self):
        """Test instance name with uppercase raises error."""
        with pytest.raises(ValidationError):
            GCPValidator.validate_instance_name("MyInstance")

    def test_valid_machine_type(self):
        """Test valid machine type passes validation."""
        machine_type = "e2-micro"
        result = GCPValidator.validate_machine_type(machine_type)
        assert result == machine_type

    def test_invalid_machine_type(self):
        """Test invalid machine type raises error."""
        with pytest.raises(ValidationError, match="Unknown GCP machine type"):
            GCPValidator.validate_machine_type("invalid-type")

    def test_valid_zone(self):
        """Test valid zone passes validation."""
        zone = "us-central1-a"
        result = GCPValidator.validate_zone(zone)
        assert result == zone

    def test_invalid_zone(self):
        """Test invalid zone raises error."""
        with pytest.raises(ValidationError, match="Invalid or uncommon GCP zone"):
            GCPValidator.validate_zone("invalid-zone")

    def test_valid_bucket_name(self):
        """Test valid bucket name passes validation."""
        bucket = "my-test-bucket"
        result = GCPValidator.validate_bucket_name(bucket)
        assert result == bucket

    def test_invalid_bucket_name_with_goog(self):
        """Test bucket name starting with 'goog' raises error."""
        with pytest.raises(ValidationError, match="cannot start with 'goog'"):
            GCPValidator.validate_bucket_name("goog-bucket")

    def test_invalid_bucket_name_with_google(self):
        """Test bucket name containing 'google' raises error."""
        with pytest.raises(ValidationError, match="cannot contain 'google'"):
            GCPValidator.validate_bucket_name("my-google-bucket")


class TestCommonValidator:
    """Test common validators."""

    def test_valid_disk_size(self):
        """Test valid disk size passes validation."""
        size = 100
        result = CommonValidator.validate_disk_size(size)
        assert result == size

    def test_disk_size_too_small(self):
        """Test disk size below minimum raises error."""
        with pytest.raises(ValidationError, match="between 1 and"):
            CommonValidator.validate_disk_size(0)

    def test_disk_size_too_large(self):
        """Test disk size above maximum raises error."""
        with pytest.raises(ValidationError, match="between 1 and"):
            CommonValidator.validate_disk_size(100000)

    def test_valid_tags(self):
        """Test valid tags pass validation."""
        tags = {'Environment': 'production', 'Application': 'web'}
        result = CommonValidator.validate_tags_labels(tags)
        assert result == tags

    def test_too_many_tags(self):
        """Test too many tags raises error."""
        tags = {f'tag{i}': f'value{i}' for i in range(51)}
        with pytest.raises(ValidationError, match="Too many tags"):
            CommonValidator.validate_tags_labels(tags)

    def test_tag_key_too_long(self):
        """Test tag key too long raises error."""
        tags = {'a' * 129: 'value'}
        with pytest.raises(ValidationError, match="Tag key too long"):
            CommonValidator.validate_tags_labels(tags)

    def test_valid_sanitized_name(self):
        """Test name sanitization."""
        name = "my-server-123"
        result = CommonValidator.sanitize_name(name)
        assert result == name

    def test_sanitize_removes_dangerous_chars(self):
        """Test that dangerous characters are removed."""
        name = "my<script>server</script>"
        result = CommonValidator.sanitize_name(name)
        assert '<' not in result
        assert '>' not in result
        assert 'myscriptserver/script' == result or 'myscriptserverscript' == result
