"""Input validation for cloud resource parameters."""

import re
from typing import Any, Optional
from cloud_automation.instance_specs import AWS_INSTANCE_TYPES, GCP_MACHINE_TYPES
from cloud_automation.exceptions import ValidationError


class AWSValidator:
    """Validators for AWS resource parameters."""

    # AWS AMI ID format: ami-[0-9a-f]{8,17}
    AMI_ID_PATTERN = re.compile(r'^ami-[0-9a-f]{8,17}$')

    # AWS Instance ID format: i-[0-9a-f]{8,17}
    INSTANCE_ID_PATTERN = re.compile(r'^i-[0-9a-f]{8,17}$')

    # AWS Volume ID format: vol-[0-9a-f]{8,17}
    VOLUME_ID_PATTERN = re.compile(r'^vol-[0-9a-f]{8,17}$')

    # AWS Security Group ID format: sg-[0-9a-f]{8,17}
    SECURITY_GROUP_PATTERN = re.compile(r'^sg-[0-9a-f]{8,17}$')

    # AWS regions
    VALID_REGIONS = {
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
        'ap-northeast-2', 'ap-south-1', 'sa-east-1', 'ca-central-1'
    }

    @staticmethod
    def validate_ami_id(ami_id: str) -> str:
        """Validate AWS AMI ID format.

        Args:
            ami_id: AMI ID to validate

        Returns:
            Validated AMI ID

        Raises:
            ValidationError: If AMI ID is invalid
        """
        if not ami_id:
            raise ValidationError("AMI ID cannot be empty")

        if not AWSValidator.AMI_ID_PATTERN.match(ami_id):
            raise ValidationError(
                f"Invalid AMI ID format: {ami_id}. "
                f"Expected format: ami-XXXXXXXX (8-17 hex digits)"
            )

        return ami_id

    @staticmethod
    def validate_instance_id(instance_id: str) -> str:
        """Validate AWS Instance ID format.

        Args:
            instance_id: Instance ID to validate

        Returns:
            Validated instance ID

        Raises:
            ValidationError: If instance ID is invalid
        """
        if not instance_id:
            raise ValidationError("Instance ID cannot be empty")

        if not AWSValidator.INSTANCE_ID_PATTERN.match(instance_id):
            raise ValidationError(
                f"Invalid Instance ID format: {instance_id}. "
                f"Expected format: i-XXXXXXXX (8-17 hex digits)"
            )

        return instance_id

    @staticmethod
    def validate_volume_id(volume_id: str) -> str:
        """Validate AWS Volume ID format.

        Args:
            volume_id: Volume ID to validate

        Returns:
            Validated volume ID

        Raises:
            ValidationError: If volume ID is invalid
        """
        if not volume_id:
            raise ValidationError("Volume ID cannot be empty")

        if not AWSValidator.VOLUME_ID_PATTERN.match(volume_id):
            raise ValidationError(
                f"Invalid Volume ID format: {volume_id}. "
                f"Expected format: vol-XXXXXXXX (8-17 hex digits)"
            )

        return volume_id

    @staticmethod
    def validate_instance_type(instance_type: str) -> str:
        """Validate AWS instance type against known types.

        Args:
            instance_type: Instance type to validate

        Returns:
            Validated instance type

        Raises:
            ValidationError: If instance type is unknown
        """
        if not instance_type:
            raise ValidationError("Instance type cannot be empty")

        if instance_type not in AWS_INSTANCE_TYPES:
            raise ValidationError(
                f"Unknown AWS instance type: {instance_type}. "
                f"Use the Instance Type Browser to find valid types."
            )

        return instance_type

    @staticmethod
    def validate_region(region: str) -> str:
        """Validate AWS region.

        Args:
            region: Region to validate

        Returns:
            Validated region

        Raises:
            ValidationError: If region is invalid
        """
        if not region:
            raise ValidationError("Region cannot be empty")

        if region not in AWSValidator.VALID_REGIONS:
            raise ValidationError(
                f"Invalid AWS region: {region}. "
                f"Valid regions: {', '.join(sorted(AWSValidator.VALID_REGIONS))}"
            )

        return region

    @staticmethod
    def validate_s3_bucket_name(bucket_name: str) -> str:
        """Validate S3 bucket name format.

        Args:
            bucket_name: Bucket name to validate

        Returns:
            Validated bucket name

        Raises:
            ValidationError: If bucket name is invalid
        """
        if not bucket_name:
            raise ValidationError("Bucket name cannot be empty")

        # S3 bucket naming rules
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValidationError(
                f"Bucket name must be between 3 and 63 characters: {bucket_name}"
            )

        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', bucket_name):
            raise ValidationError(
                f"Invalid bucket name: {bucket_name}. "
                f"Must start/end with letter or number, contain only lowercase, numbers, hyphens, and dots"
            )

        if '..' in bucket_name or '.-' in bucket_name or '-.' in bucket_name:
            raise ValidationError(f"Bucket name cannot have consecutive special characters: {bucket_name}")

        # Cannot look like IP address
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', bucket_name):
            raise ValidationError(f"Bucket name cannot be formatted as IP address: {bucket_name}")

        return bucket_name


class GCPValidator:
    """Validators for GCP resource parameters."""

    # GCP resource name pattern: lowercase, hyphens, numbers
    RESOURCE_NAME_PATTERN = re.compile(r'^[a-z]([-a-z0-9]*[a-z0-9])?$')

    # GCP Project ID pattern
    PROJECT_ID_PATTERN = re.compile(r'^[a-z]([-a-z0-9]*[a-z0-9])?$')

    # GCP zones (common ones, not exhaustive)
    VALID_ZONES = {
        'us-central1-a', 'us-central1-b', 'us-central1-c', 'us-central1-f',
        'us-east1-b', 'us-east1-c', 'us-east1-d',
        'us-west1-a', 'us-west1-b', 'us-west1-c',
        'europe-west1-b', 'europe-west1-c', 'europe-west1-d',
        'asia-east1-a', 'asia-east1-b', 'asia-east1-c',
        'asia-southeast1-a', 'asia-southeast1-b', 'asia-southeast1-c'
    }

    @staticmethod
    def validate_project_id(project_id: str) -> str:
        """Validate GCP project ID format.

        Args:
            project_id: Project ID to validate

        Returns:
            Validated project ID

        Raises:
            ValidationError: If project ID is invalid
        """
        if not project_id:
            raise ValidationError("Project ID cannot be empty")

        if len(project_id) < 6 or len(project_id) > 30:
            raise ValidationError(
                f"Project ID must be between 6 and 30 characters: {project_id}"
            )

        if not GCPValidator.PROJECT_ID_PATTERN.match(project_id):
            raise ValidationError(
                f"Invalid project ID: {project_id}. "
                f"Must start with letter, contain only lowercase, numbers, and hyphens"
            )

        return project_id

    @staticmethod
    def validate_instance_name(name: str) -> str:
        """Validate GCP instance name format.

        Args:
            name: Instance name to validate

        Returns:
            Validated name

        Raises:
            ValidationError: If name is invalid
        """
        if not name:
            raise ValidationError("Instance name cannot be empty")

        if len(name) > 63:
            raise ValidationError(
                f"Instance name must be 63 characters or less: {name} ({len(name)} chars)"
            )

        if not GCPValidator.RESOURCE_NAME_PATTERN.match(name):
            raise ValidationError(
                f"Invalid instance name: {name}. "
                f"Must start with lowercase letter, contain only lowercase, numbers, and hyphens"
            )

        return name

    @staticmethod
    def validate_machine_type(machine_type: str) -> str:
        """Validate GCP machine type against known types.

        Args:
            machine_type: Machine type to validate

        Returns:
            Validated machine type

        Raises:
            ValidationError: If machine type is unknown
        """
        if not machine_type:
            raise ValidationError("Machine type cannot be empty")

        if machine_type not in GCP_MACHINE_TYPES:
            raise ValidationError(
                f"Unknown GCP machine type: {machine_type}. "
                f"Use the Instance Type Browser to find valid types."
            )

        return machine_type

    @staticmethod
    def validate_zone(zone: str) -> str:
        """Validate GCP zone.

        Args:
            zone: Zone to validate

        Returns:
            Validated zone

        Raises:
            ValidationError: If zone is invalid
        """
        if not zone:
            raise ValidationError("Zone cannot be empty")

        if zone not in GCPValidator.VALID_ZONES:
            raise ValidationError(
                f"Invalid or uncommon GCP zone: {zone}. "
                f"Common zones: {', '.join(sorted(list(GCPValidator.VALID_ZONES)[:10]))}"
            )

        return zone

    @staticmethod
    def validate_bucket_name(bucket_name: str) -> str:
        """Validate GCP Cloud Storage bucket name format.

        Args:
            bucket_name: Bucket name to validate

        Returns:
            Validated bucket name

        Raises:
            ValidationError: If bucket name is invalid
        """
        if not bucket_name:
            raise ValidationError("Bucket name cannot be empty")

        # GCP bucket naming rules (similar to S3 but with some differences)
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValidationError(
                f"Bucket name must be between 3 and 63 characters: {bucket_name}"
            )

        if not re.match(r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$', bucket_name):
            raise ValidationError(
                f"Invalid bucket name: {bucket_name}. "
                f"Must start/end with letter or number, contain only lowercase, numbers, dots, hyphens, underscores"
            )

        # Cannot start with 'goog' prefix
        if bucket_name.startswith('goog'):
            raise ValidationError(f"Bucket name cannot start with 'goog': {bucket_name}")

        # Cannot contain 'google' substring
        if 'google' in bucket_name:
            raise ValidationError(f"Bucket name cannot contain 'google': {bucket_name}")

        return bucket_name


class CommonValidator:
    """Common validators for both AWS and GCP."""

    @staticmethod
    def validate_disk_size(size_gb: int, min_size: int = 1, max_size: int = 65536) -> int:
        """Validate disk size in GB.

        Args:
            size_gb: Size in GB
            min_size: Minimum allowed size
            max_size: Maximum allowed size

        Returns:
            Validated size

        Raises:
            ValidationError: If size is invalid
        """
        if not isinstance(size_gb, int):
            raise ValidationError(f"Disk size must be an integer: {size_gb}")

        if size_gb < min_size or size_gb > max_size:
            raise ValidationError(
                f"Disk size must be between {min_size} and {max_size} GB: {size_gb}"
            )

        return size_gb

    @staticmethod
    def validate_tags_labels(tags: dict, max_count: int = 50) -> dict:
        """Validate resource tags/labels.

        Args:
            tags: Dictionary of tags/labels
            max_count: Maximum number of tags allowed

        Returns:
            Validated tags

        Raises:
            ValidationError: If tags are invalid
        """
        if not isinstance(tags, dict):
            raise ValidationError(f"Tags must be a dictionary: {type(tags)}")

        if len(tags) > max_count:
            raise ValidationError(f"Too many tags: {len(tags)} (max: {max_count})")

        for key, value in tags.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidationError(f"Tag keys and values must be strings: {key}={value}")

            if len(key) > 128:
                raise ValidationError(f"Tag key too long (max 128 chars): {key}")

            if len(value) > 256:
                raise ValidationError(f"Tag value too long (max 256 chars): {value}")

        return tags

    @staticmethod
    def sanitize_name(name: str, max_length: int = 255) -> str:
        """Sanitize resource name for safety.

        Args:
            name: Name to sanitize
            max_length: Maximum length

        Returns:
            Sanitized name

        Raises:
            ValidationError: If name cannot be sanitized
        """
        if not name:
            raise ValidationError("Name cannot be empty")

        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name)

        if len(sanitized) > max_length:
            raise ValidationError(
                f"Name too long: {len(sanitized)} characters (max: {max_length})"
            )

        if not sanitized:
            raise ValidationError("Name contains only invalid characters")

        return sanitized
