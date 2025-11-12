"""Configuration template management for saving and loading VM/storage setups."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class TemplateManager:
    """Manages configuration templates for VMs and storage."""

    def __init__(self, templates_dir: str = "configs/templates"):
        """Initialize template manager.

        Args:
            templates_dir: Directory to store template files
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Create provider subdirectories
        (self.templates_dir / "aws").mkdir(exist_ok=True)
        (self.templates_dir / "gcp").mkdir(exist_ok=True)

    def save_template(
        self,
        name: str,
        provider: str,
        config: Dict[str, Any],
        description: str = ""
    ) -> str:
        """Save a configuration template.

        Args:
            name: Template name (used as filename)
            provider: Cloud provider ('aws' or 'gcp')
            config: Configuration dictionary
            description: Optional template description

        Returns:
            Path to saved template file

        Raises:
            ValueError: If provider is invalid
        """
        if provider.lower() not in ['aws', 'gcp']:
            raise ValueError(f"Invalid provider: {provider}. Must be 'aws' or 'gcp'")

        # Create template data
        template_data = {
            'name': name,
            'provider': provider.lower(),
            'description': description,
            'created_at': datetime.now().isoformat(),
            'config': config
        }

        # Generate filename from name
        filename = self._sanitize_filename(name) + ".yaml"
        filepath = self.templates_dir / provider.lower() / filename

        # Save to YAML
        with open(filepath, 'w') as f:
            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)

        return str(filepath)

    def load_template(self, name: str, provider: str) -> Dict[str, Any]:
        """Load a configuration template.

        Args:
            name: Template name
            provider: Cloud provider ('aws' or 'gcp')

        Returns:
            Template configuration dictionary

        Raises:
            FileNotFoundError: If template doesn't exist
            ValueError: If provider is invalid
        """
        if provider.lower() not in ['aws', 'gcp']:
            raise ValueError(f"Invalid provider: {provider}. Must be 'aws' or 'gcp'")

        filename = self._sanitize_filename(name) + ".yaml"
        filepath = self.templates_dir / provider.lower() / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Template not found: {name}")

        with open(filepath, 'r') as f:
            template_data = yaml.safe_load(f)

        return template_data

    def list_templates(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available templates.

        Args:
            provider: Optional filter by provider ('aws' or 'gcp')

        Returns:
            List of template metadata dictionaries
        """
        templates = []

        if provider:
            providers = [provider.lower()]
        else:
            providers = ['aws', 'gcp']

        for prov in providers:
            provider_dir = self.templates_dir / prov
            if not provider_dir.exists():
                continue

            for filepath in provider_dir.glob("*.yaml"):
                try:
                    with open(filepath, 'r') as f:
                        data = yaml.safe_load(f)

                    templates.append({
                        'name': data.get('name', filepath.stem),
                        'provider': prov,
                        'description': data.get('description', ''),
                        'created_at': data.get('created_at', ''),
                        'filepath': str(filepath)
                    })
                except Exception:
                    # Skip invalid template files
                    continue

        return sorted(templates, key=lambda x: x.get('created_at', ''), reverse=True)

    def delete_template(self, name: str, provider: str) -> bool:
        """Delete a configuration template.

        Args:
            name: Template name
            provider: Cloud provider ('aws' or 'gcp')

        Returns:
            True if deleted successfully

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        if provider.lower() not in ['aws', 'gcp']:
            raise ValueError(f"Invalid provider: {provider}. Must be 'aws' or 'gcp'")

        filename = self._sanitize_filename(name) + ".yaml"
        filepath = self.templates_dir / provider.lower() / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Template not found: {name}")

        filepath.unlink()
        return True

    def template_exists(self, name: str, provider: str) -> bool:
        """Check if a template exists.

        Args:
            name: Template name
            provider: Cloud provider ('aws' or 'gcp')

        Returns:
            True if template exists
        """
        filename = self._sanitize_filename(name) + ".yaml"
        filepath = self.templates_dir / provider.lower() / filename
        return filepath.exists()

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize template name for use as filename.

        Args:
            name: Template name

        Returns:
            Sanitized filename (lowercase, hyphens, alphanumeric)
        """
        # Convert to lowercase
        filename = name.lower()

        # Replace spaces and underscores with hyphens
        filename = filename.replace(' ', '-').replace('_', '-')

        # Remove any characters that aren't alphanumeric or hyphens
        filename = ''.join(c for c in filename if c.isalnum() or c == '-')

        # Remove consecutive hyphens
        while '--' in filename:
            filename = filename.replace('--', '-')

        # Strip leading/trailing hyphens
        filename = filename.strip('-')

        return filename or 'unnamed-template'


def create_aws_vm_template(
    name: str,
    instance_type: str,
    region: str,
    ami: Optional[str] = None,
    key_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    spot_instance: bool = False
) -> Dict[str, Any]:
    """Helper to create AWS VM template configuration.

    Args:
        name: Instance name
        instance_type: EC2 instance type
        region: AWS region
        ami: AMI ID (optional)
        key_name: SSH key pair name (optional)
        tags: Resource tags (optional)
        spot_instance: Request spot instance (optional)

    Returns:
        Template configuration dictionary
    """
    config = {
        'resource_type': 'vm',
        'region': region,
        'vm': {
            'name': name,
            'instance_type': instance_type,
            'spot_instance': spot_instance
        }
    }

    if ami:
        config['vm']['ami'] = ami
    if key_name:
        config['vm']['key_name'] = key_name
    if tags:
        config['vm']['tags'] = tags

    return config


def create_gcp_vm_template(
    name: str,
    machine_type: str,
    zone: str,
    project_id: str,
    image_family: Optional[str] = None,
    image_name: Optional[str] = None,
    image_project: Optional[str] = None,
    disk_size_gb: int = 10,
    external_ip: bool = True,
    labels: Optional[Dict[str, str]] = None,
    spot_vm: bool = False
) -> Dict[str, Any]:
    """Helper to create GCP VM template configuration.

    Args:
        name: Instance name
        machine_type: GCP machine type
        zone: GCP zone
        project_id: GCP project ID
        image_family: Image family (optional)
        image_name: Specific image name (optional)
        image_project: Image project (optional)
        disk_size_gb: Boot disk size
        external_ip: Assign external IP
        labels: Resource labels (optional)
        spot_vm: Use Spot VM (optional)

    Returns:
        Template configuration dictionary
    """
    config = {
        'resource_type': 'vm',
        'project_id': project_id,
        'zone': zone,
        'vm': {
            'name': name,
            'machine_type': machine_type,
            'disk_size_gb': disk_size_gb,
            'external_ip': external_ip,
            'spot_vm': spot_vm
        }
    }

    if image_family:
        config['vm']['image_family'] = image_family
    if image_name:
        config['vm']['image_name'] = image_name
    if image_project:
        config['vm']['image_project'] = image_project
    if labels:
        config['vm']['labels'] = labels

    return config


def create_aws_storage_template(
    bucket_name: Optional[str] = None,
    volume_name: Optional[str] = None,
    region: str = "us-east-1",
    versioning: bool = False,
    encryption: bool = True,
    volume_size: int = 100,
    volume_type: str = "gp3"
) -> Dict[str, Any]:
    """Helper to create AWS storage template configuration.

    Args:
        bucket_name: S3 bucket name (optional)
        volume_name: EBS volume name (optional)
        region: AWS region
        versioning: Enable S3 versioning
        encryption: Enable S3 encryption
        volume_size: EBS volume size in GB
        volume_type: EBS volume type

    Returns:
        Template configuration dictionary
    """
    config = {
        'resource_type': 'storage',
        'region': region,
        'storage': {}
    }

    if bucket_name:
        config['storage']['s3'] = {
            'bucket_name': bucket_name,
            'versioning': versioning,
            'encryption': encryption
        }

    if volume_name:
        config['storage']['ebs'] = {
            'volume_name': volume_name,
            'size': volume_size,
            'volume_type': volume_type
        }

    return config


def create_gcp_storage_template(
    bucket_name: Optional[str] = None,
    disk_name: Optional[str] = None,
    project_id: str = "",
    zone: str = "us-central1-a",
    location: str = "US",
    storage_class: str = "STANDARD",
    versioning: bool = False,
    disk_size_gb: int = 100,
    disk_type: str = "pd-standard"
) -> Dict[str, Any]:
    """Helper to create GCP storage template configuration.

    Args:
        bucket_name: Cloud Storage bucket name (optional)
        disk_name: Persistent disk name (optional)
        project_id: GCP project ID
        zone: GCP zone
        location: Bucket location
        storage_class: Bucket storage class
        versioning: Enable bucket versioning
        disk_size_gb: Disk size in GB
        disk_type: Disk type

    Returns:
        Template configuration dictionary
    """
    config = {
        'resource_type': 'storage',
        'project_id': project_id,
        'zone': zone,
        'storage': {}
    }

    if bucket_name:
        config['storage']['bucket'] = {
            'bucket_name': bucket_name,
            'location': location,
            'storage_class': storage_class,
            'versioning': versioning
        }

    if disk_name:
        config['storage']['disk'] = {
            'disk_name': disk_name,
            'size_gb': disk_size_gb,
            'disk_type': disk_type
        }

    return config
