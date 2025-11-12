"""Resource quota and cost control system."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from cloud_automation.instance_specs import AWS_INSTANCE_TYPES, GCP_MACHINE_TYPES


@dataclass
class ResourceQuota:
    """Resource usage quotas and limits."""

    # Daily limits
    max_instances_per_day: int = 10
    max_storage_gb_per_day: int = 1000

    # Per-operation limits
    max_disk_size_gb: int = 500
    warn_expensive_instances: bool = True

    # Cost thresholds (per instance type category)
    expensive_instance_threshold: str = "medium"  # small, medium, large

    # Current usage (resets daily)
    instances_created_today: int = 0
    storage_provisioned_today_gb: int = 0
    last_reset_date: str = ""


class QuotaExceeded(Exception):
    """Raised when resource quota is exceeded."""
    pass


class CostWarning(Warning):
    """Warning for potentially expensive operations."""
    pass


class QuotaManager:
    """Manages resource quotas and cost controls."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize quota manager.

        Args:
            config_dir: Directory for quota tracking (defaults to ~/.cloud-automation)
        """
        if config_dir is None:
            self.config_dir = Path.home() / '.cloud-automation'
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.quota_file = self.config_dir / 'quota.json'
        self.quota = self._load_or_create_quota()

    def _load_or_create_quota(self) -> ResourceQuota:
        """Load existing quota or create default.

        Returns:
            ResourceQuota object
        """
        if self.quota_file.exists():
            try:
                with open(self.quota_file, 'r') as f:
                    data = json.load(f)
                quota = ResourceQuota(**data)

                # Reset daily counters if it's a new day
                if quota.last_reset_date != str(datetime.now().date()):
                    quota.instances_created_today = 0
                    quota.storage_provisioned_today_gb = 0
                    quota.last_reset_date = str(datetime.now().date())
                    self._save_quota(quota)

                return quota
            except Exception:
                # If loading fails, create new
                return self._create_default_quota()
        else:
            return self._create_default_quota()

    def _create_default_quota(self) -> ResourceQuota:
        """Create default quota with today's date.

        Returns:
            New ResourceQuota object
        """
        quota = ResourceQuota(last_reset_date=str(datetime.now().date()))
        self._save_quota(quota)
        return quota

    def _save_quota(self, quota: ResourceQuota) -> None:
        """Save quota to disk.

        Args:
            quota: ResourceQuota to save
        """
        with open(self.quota_file, 'w') as f:
            json.dump(asdict(quota), f, indent=2)

    def check_instance_quota(self, instance_type: str, provider: str) -> None:
        """Check if instance creation is within quota.

        Args:
            instance_type: Instance/machine type
            provider: Cloud provider ('aws' or 'gcp')

        Raises:
            QuotaExceeded: If quota would be exceeded
            CostWarning: If instance type is expensive (warning only)
        """
        # Check daily instance limit
        if self.quota.instances_created_today >= self.quota.max_instances_per_day:
            raise QuotaExceeded(
                f"Daily instance limit reached: {self.quota.max_instances_per_day}. "
                f"Limit resets tomorrow."
            )

        # Warn about expensive instances
        if self.quota.warn_expensive_instances:
            if self._is_expensive_instance(instance_type, provider):
                import warnings
                warnings.warn(
                    f"WARNING: {instance_type} is considered an expensive instance type. "
                    f"This may result in significant costs. Proceed with caution.",
                    CostWarning
                )

    def check_storage_quota(self, size_gb: int) -> None:
        """Check if storage provisioning is within quota.

        Args:
            size_gb: Storage size in GB

        Raises:
            QuotaExceeded: If quota would be exceeded
        """
        # Check single disk size limit
        if size_gb > self.quota.max_disk_size_gb:
            raise QuotaExceeded(
                f"Disk size {size_gb}GB exceeds maximum allowed: {self.quota.max_disk_size_gb}GB. "
                f"For larger disks, adjust quota limits."
            )

        # Check daily storage limit
        if (self.quota.storage_provisioned_today_gb + size_gb) > self.quota.max_storage_gb_per_day:
            raise QuotaExceeded(
                f"Daily storage limit would be exceeded: "
                f"{self.quota.storage_provisioned_today_gb + size_gb}GB / {self.quota.max_storage_gb_per_day}GB. "
                f"Limit resets tomorrow."
            )

    def record_instance_created(self) -> None:
        """Record that an instance was created."""
        self.quota.instances_created_today += 1
        self._save_quota(self.quota)

    def record_storage_provisioned(self, size_gb: int) -> None:
        """Record storage provisioning.

        Args:
            size_gb: Storage size in GB
        """
        self.quota.storage_provisioned_today_gb += size_gb
        self._save_quota(self.quota)

    def _is_expensive_instance(self, instance_type: str, provider: str) -> bool:
        """Determine if instance type is expensive.

        Args:
            instance_type: Instance/machine type
            provider: Cloud provider

        Returns:
            True if expensive, False otherwise
        """
        expensive_categories = {
            "small": [],
            "medium": ["Compute Optimized", "Memory Optimized"],
            "large": ["Compute Optimized", "Memory Optimized", "General Purpose"]
        }

        threshold = self.quota.expensive_instance_threshold
        categories_to_warn = expensive_categories.get(threshold, [])

        if provider == "aws":
            specs = AWS_INSTANCE_TYPES.get(instance_type)
            if specs:
                # Check if category is expensive
                if specs['category'] in categories_to_warn:
                    return True
                # Check vCPU count (>= 8 vCPUs is expensive)
                if specs['vcpu'] >= 8:
                    return True
                # Check memory (>= 32GB is expensive)
                if specs['memory_gb'] >= 32:
                    return True

        elif provider == "gcp":
            specs = GCP_MACHINE_TYPES.get(instance_type)
            if specs:
                # Check if category is expensive
                if specs['category'] in categories_to_warn:
                    return True
                # Check vCPU count
                if specs['vcpu'] >= 8:
                    return True
                # Check memory
                if specs['memory_gb'] >= 32:
                    return True

        return False

    def get_usage_summary(self) -> Dict[str, any]:
        """Get current usage summary.

        Returns:
            Dictionary with usage information
        """
        return {
            'instances_today': {
                'used': self.quota.instances_created_today,
                'limit': self.quota.max_instances_per_day,
                'remaining': self.quota.max_instances_per_day - self.quota.instances_created_today
            },
            'storage_today_gb': {
                'used': self.quota.storage_provisioned_today_gb,
                'limit': self.quota.max_storage_gb_per_day,
                'remaining': self.quota.max_storage_gb_per_day - self.quota.storage_provisioned_today_gb
            },
            'reset_date': self.quota.last_reset_date,
            'next_reset': str((datetime.now() + timedelta(days=1)).date())
        }

    def update_limits(
        self,
        max_instances_per_day: Optional[int] = None,
        max_storage_gb_per_day: Optional[int] = None,
        max_disk_size_gb: Optional[int] = None,
        expensive_instance_threshold: Optional[str] = None
    ) -> None:
        """Update quota limits.

        Args:
            max_instances_per_day: Maximum instances per day
            max_storage_gb_per_day: Maximum storage GB per day
            max_disk_size_gb: Maximum single disk size
            expensive_instance_threshold: Cost warning threshold (small/medium/large)
        """
        if max_instances_per_day is not None:
            self.quota.max_instances_per_day = max_instances_per_day

        if max_storage_gb_per_day is not None:
            self.quota.max_storage_gb_per_day = max_storage_gb_per_day

        if max_disk_size_gb is not None:
            self.quota.max_disk_size_gb = max_disk_size_gb

        if expensive_instance_threshold is not None:
            if expensive_instance_threshold not in ['small', 'medium', 'large', 'none']:
                raise ValueError(f"Invalid threshold: {expensive_instance_threshold}")
            self.quota.expensive_instance_threshold = expensive_instance_threshold

        self._save_quota(self.quota)
