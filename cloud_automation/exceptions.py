"""Custom exception types for cloud automation."""

from typing import Optional


class CloudAutomationError(Exception):
    """Base exception for cloud automation errors."""
    pass


# Credential Errors
class CredentialError(CloudAutomationError):
    """Base class for credential-related errors."""
    pass


class CredentialNotFoundError(CredentialError):
    """Raised when credentials are not found or not configured."""
    pass


class CredentialDecryptionError(CredentialError):
    """Raised when credential decryption fails."""
    pass


class CredentialValidationError(CredentialError):
    """Raised when credentials fail validation."""
    pass


# Validation Errors
class ValidationError(CloudAutomationError):
    """Raised when input validation fails."""
    pass


# Provisioning Errors
class ProvisioningError(CloudAutomationError):
    """Base class for provisioning errors."""
    pass


class InstanceCreationError(ProvisioningError):
    """Raised when instance creation fails."""
    pass


class StorageProvisioningError(ProvisioningError):
    """Raised when storage provisioning fails."""
    pass


class ResourceNotFoundError(ProvisioningError):
    """Raised when a cloud resource is not found."""
    pass


class ResourceStateError(ProvisioningError):
    """Raised when resource is in incorrect state for operation."""
    pass


# Quota Errors
class QuotaError(CloudAutomationError):
    """Base class for quota-related errors."""
    pass


class QuotaExceeded(QuotaError):
    """Raised when resource quota is exceeded."""
    pass


class CostThresholdExceeded(QuotaError):
    """Raised when operation would exceed cost threshold."""
    pass


# Connection Errors
class ConnectionError(CloudAutomationError):
    """Raised when cloud provider connection fails."""
    pass


class AWSConnectionError(ConnectionError):
    """Raised when AWS connection fails."""
    pass


class GCPConnectionError(ConnectionError):
    """Raised when GCP connection fails."""
    pass


# API Errors
class APIError(CloudAutomationError):
    """Base class for cloud provider API errors."""
    pass


class AWSAPIError(APIError):
    """Raised when AWS API call fails."""

    def __init__(self, message: str, error_code: Optional[str] = None, status_code: Optional[int] = None):
        """Initialize AWS API error.

        Args:
            message: Error message
            error_code: AWS error code (e.g., InvalidAMIID.NotFound)
            status_code: HTTP status code
        """
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code


class GCPAPIError(APIError):
    """Raised when GCP API call fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize GCP API error.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        super().__init__(message)
        self.status_code = status_code


# Configuration Errors
class ConfigurationError(CloudAutomationError):
    """Raised when configuration is invalid or missing."""
    pass


class InvalidRegionError(ConfigurationError):
    """Raised when region/zone is invalid."""
    pass


class InvalidInstanceTypeError(ConfigurationError):
    """Raised when instance/machine type is invalid."""
    pass
