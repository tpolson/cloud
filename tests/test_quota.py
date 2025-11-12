"""Tests for resource quota and cost control."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from cloud_automation.quota import QuotaManager, QuotaExceeded, CostWarning


class TestQuotaManager:
    """Test quota management and cost controls."""

    @pytest.fixture
    def temp_quota_manager(self):
        """Create temporary quota manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield QuotaManager(config_dir=Path(tmpdir))

    def test_default_quota_creation(self, temp_quota_manager):
        """Test that default quota is created."""
        quota = temp_quota_manager.quota

        assert quota.max_instances_per_day == 10
        assert quota.max_storage_gb_per_day == 1000
        assert quota.instances_created_today == 0
        assert quota.storage_provisioned_today_gb == 0

    def test_quota_file_created(self, temp_quota_manager):
        """Test that quota file is created."""
        assert temp_quota_manager.quota_file.exists()

    def test_check_instance_quota_within_limit(self, temp_quota_manager):
        """Test instance quota check passes when within limit."""
        # Should not raise exception
        temp_quota_manager.check_instance_quota("t2.micro", "aws")

    def test_check_instance_quota_exceeds_limit(self, temp_quota_manager):
        """Test instance quota check fails when limit exceeded."""
        # Set usage to limit
        temp_quota_manager.quota.instances_created_today = 10

        with pytest.raises(QuotaExceeded, match="Daily instance limit reached"):
            temp_quota_manager.check_instance_quota("t2.micro", "aws")

    def test_expensive_instance_warning(self, temp_quota_manager):
        """Test warning for expensive instance types."""
        # Enable warnings
        temp_quota_manager.quota.warn_expensive_instances = True
        temp_quota_manager.quota.expensive_instance_threshold = "medium"

        # Should warn for compute optimized instances
        with pytest.warns(CostWarning, match="expensive instance type"):
            temp_quota_manager.check_instance_quota("c5.xlarge", "aws")

    def test_check_storage_quota_within_limit(self, temp_quota_manager):
        """Test storage quota check passes when within limit."""
        # Should not raise exception
        temp_quota_manager.check_storage_quota(100)

    def test_check_storage_quota_single_disk_too_large(self, temp_quota_manager):
        """Test storage quota check fails for oversized disk."""
        with pytest.raises(QuotaExceeded, match="exceeds maximum allowed"):
            temp_quota_manager.check_storage_quota(600)  # Max is 500

    def test_check_storage_quota_exceeds_daily_limit(self, temp_quota_manager):
        """Test storage quota check fails when daily limit exceeded."""
        # Set usage near limit
        temp_quota_manager.quota.storage_provisioned_today_gb = 950

        with pytest.raises(QuotaExceeded, match="Daily storage limit would be exceeded"):
            temp_quota_manager.check_storage_quota(100)  # Would total 1050

    def test_record_instance_created(self, temp_quota_manager):
        """Test recording instance creation."""
        initial = temp_quota_manager.quota.instances_created_today

        temp_quota_manager.record_instance_created()

        assert temp_quota_manager.quota.instances_created_today == initial + 1

    def test_record_storage_provisioned(self, temp_quota_manager):
        """Test recording storage provisioning."""
        initial = temp_quota_manager.quota.storage_provisioned_today_gb

        temp_quota_manager.record_storage_provisioned(50)

        assert temp_quota_manager.quota.storage_provisioned_today_gb == initial + 50

    def test_get_usage_summary(self, temp_quota_manager):
        """Test getting usage summary."""
        temp_quota_manager.record_instance_created()
        temp_quota_manager.record_storage_provisioned(100)

        summary = temp_quota_manager.get_usage_summary()

        assert summary['instances_today']['used'] == 1
        assert summary['instances_today']['limit'] == 10
        assert summary['instances_today']['remaining'] == 9

        assert summary['storage_today_gb']['used'] == 100
        assert summary['storage_today_gb']['limit'] == 1000
        assert summary['storage_today_gb']['remaining'] == 900

    def test_update_limits(self, temp_quota_manager):
        """Test updating quota limits."""
        temp_quota_manager.update_limits(
            max_instances_per_day=20,
            max_storage_gb_per_day=2000,
            max_disk_size_gb=1000
        )

        assert temp_quota_manager.quota.max_instances_per_day == 20
        assert temp_quota_manager.quota.max_storage_gb_per_day == 2000
        assert temp_quota_manager.quota.max_disk_size_gb == 1000

    def test_quota_reset_on_new_day(self):
        """Test that quota resets on new day."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QuotaManager(config_dir=Path(tmpdir))

            # Record some usage
            manager.record_instance_created()
            manager.record_storage_provisioned(100)

            assert manager.quota.instances_created_today == 1
            assert manager.quota.storage_provisioned_today_gb == 100

            # Simulate new day by manually changing last_reset_date
            manager.quota.last_reset_date = "2000-01-01"
            manager._save_quota(manager.quota)

            # Create new manager (simulates app restart on new day)
            manager2 = QuotaManager(config_dir=Path(tmpdir))

            # Counters should be reset
            assert manager2.quota.instances_created_today == 0
            assert manager2.quota.storage_provisioned_today_gb == 0

    def test_is_expensive_instance_aws_large_vcpu(self, temp_quota_manager):
        """Test expensive instance detection for high vCPU count."""
        # m5.2xlarge has 8 vCPUs - should be flagged as expensive
        result = temp_quota_manager._is_expensive_instance("m5.2xlarge", "aws")
        assert result is True

    def test_is_expensive_instance_gcp_large_memory(self, temp_quota_manager):
        """Test expensive instance detection for high memory."""
        # n2-highmem-8 has 64GB memory - should be flagged as expensive
        result = temp_quota_manager._is_expensive_instance("n2-highmem-8", "gcp")
        assert result is True

    def test_is_expensive_instance_small_type(self, temp_quota_manager):
        """Test that small instances are not flagged as expensive."""
        result = temp_quota_manager._is_expensive_instance("t2.micro", "aws")
        assert result is False

    def test_invalid_threshold_raises_error(self, temp_quota_manager):
        """Test that invalid threshold raises error."""
        with pytest.raises(ValueError, match="Invalid threshold"):
            temp_quota_manager.update_limits(expensive_instance_threshold="invalid")
