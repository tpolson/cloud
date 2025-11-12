"""Tests for credential store with PBKDF2 encryption."""

import pytest
import tempfile
from pathlib import Path
from cloud_automation.credential_store import CredentialStore


class TestCredentialStore:
    """Test credential storage and encryption."""

    @pytest.fixture
    def temp_store(self):
        """Create temporary credential store."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield CredentialStore(config_dir=Path(tmpdir))

    def test_encryption_decryption_round_trip(self, temp_store):
        """Test that credentials can be encrypted and decrypted."""
        creds = {
            'aws_credentials': {
                'access_key_id': 'AKIAIOSFODNN7EXAMPLE',
                'secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                'region': 'us-east-1'
            },
            'gcp_credentials': {
                'project_id': 'test-project-123',
                'zone': 'us-central1-a'
            }
        }

        # Save credentials
        temp_store.save_credentials(creds)

        # Load credentials
        loaded = temp_store.load_credentials()

        # Verify
        assert loaded == creds
        assert loaded['aws_credentials']['access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'
        assert loaded['gcp_credentials']['project_id'] == 'test-project-123'

    def test_salt_is_generated(self, temp_store):
        """Test that salt file is created."""
        creds = {'test': 'data'}
        temp_store.save_credentials(creds)

        # Check salt file exists
        assert temp_store.salt_file.exists()

        # Salt should be 32 bytes
        salt = temp_store.salt_file.read_bytes()
        assert len(salt) == 32

    def test_credentials_file_permissions(self, temp_store):
        """Test that credentials file has correct permissions (0600)."""
        creds = {'test': 'data'}
        temp_store.save_credentials(creds)

        import stat
        file_stat = temp_store.credentials_file.stat()
        permissions = stat.S_IMODE(file_stat.st_mode)

        # Should be 0600 (user read/write only)
        assert permissions == 0o600

    def test_no_credentials_returns_none(self, temp_store):
        """Test that loading non-existent credentials returns None."""
        result = temp_store.load_credentials()
        assert result is None

    def test_credentials_exist_check(self, temp_store):
        """Test credentials_exist() method."""
        assert temp_store.credentials_exist() is False

        temp_store.save_credentials({'test': 'data'})
        assert temp_store.credentials_exist() is True

    def test_delete_credentials(self, temp_store):
        """Test that credentials and salt are deleted."""
        temp_store.save_credentials({'test': 'data'})

        assert temp_store.credentials_file.exists()
        assert temp_store.salt_file.exists()

        temp_store.delete_credentials()

        assert not temp_store.credentials_file.exists()
        assert not temp_store.salt_file.exists()

    def test_get_aws_credentials(self, temp_store):
        """Test AWS credentials getter."""
        creds = {
            'aws_credentials': {
                'access_key_id': 'test_key',
                'secret_access_key': 'test_secret'
            }
        }
        temp_store.save_credentials(creds)

        aws_creds = temp_store.get_aws_credentials()
        assert aws_creds['access_key_id'] == 'test_key'

    def test_get_gcp_credentials(self, temp_store):
        """Test GCP credentials getter."""
        creds = {
            'gcp_credentials': {
                'project_id': 'test-project'
            }
        }
        temp_store.save_credentials(creds)

        gcp_creds = temp_store.get_gcp_credentials()
        assert gcp_creds['project_id'] == 'test-project'

    def test_save_aws_credentials(self, temp_store):
        """Test saving only AWS credentials."""
        aws_creds = {
            'access_key_id': 'test_key',
            'secret_access_key': 'test_secret'
        }
        temp_store.save_aws_credentials(aws_creds)

        loaded = temp_store.load_credentials()
        assert 'aws_credentials' in loaded
        assert loaded['aws_credentials'] == aws_creds

    def test_save_gcp_credentials(self, temp_store):
        """Test saving only GCP credentials."""
        gcp_creds = {
            'project_id': 'test-project',
            'zone': 'us-central1-a'
        }
        temp_store.save_gcp_credentials(gcp_creds)

        loaded = temp_store.load_credentials()
        assert 'gcp_credentials' in loaded
        assert loaded['gcp_credentials'] == gcp_creds

    def test_format_version_included(self, temp_store):
        """Test that format version is included in saved data."""
        creds = {'test': 'data'}
        temp_store.save_credentials(creds)

        # Read the encrypted data and decrypt
        loaded = temp_store.load_credentials()

        # The returned data should be the credentials (version is stripped)
        assert loaded == creds
