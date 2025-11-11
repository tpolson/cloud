"""Configuration management for cloud automation."""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file (YAML)
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, 'r') as f:
            self.config = yaml.safe_load(f)

        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'aws.region')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    def get_aws_config(self) -> Dict[str, Any]:
        """Get AWS-specific configuration.

        Returns:
            AWS configuration dictionary
        """
        return self.config.get('aws', {})

    def get_gcp_config(self) -> Dict[str, Any]:
        """Get GCP-specific configuration.

        Returns:
            GCP configuration dictionary
        """
        return self.config.get('gcp', {})

    @staticmethod
    def get_aws_credentials() -> Dict[str, Optional[str]]:
        """Get AWS credentials from environment or AWS config.

        Returns:
            Dictionary with access_key_id and secret_access_key
        """
        return {
            'access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
            'secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            'region': os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
        }

    @staticmethod
    def get_gcp_credentials() -> Dict[str, Optional[str]]:
        """Get GCP credentials from environment.

        Returns:
            Dictionary with credentials path and project info
        """
        return {
            'credentials_path': os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
            'project_id': os.environ.get('GCP_PROJECT_ID'),
        }

    def validate_aws_config(self) -> bool:
        """Validate AWS configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        aws_config = self.get_aws_config()

        if not aws_config:
            raise ValueError("AWS configuration not found")

        required_fields = ['region']
        for field in required_fields:
            if field not in aws_config:
                raise ValueError(f"Missing required AWS config field: {field}")

        return True

    def validate_gcp_config(self) -> bool:
        """Validate GCP configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        gcp_config = self.get_gcp_config()

        if not gcp_config:
            raise ValueError("GCP configuration not found")

        required_fields = ['project_id']
        for field in required_fields:
            if field not in gcp_config:
                raise ValueError(f"Missing required GCP config field: {field}")

        return True
