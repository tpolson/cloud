"""Secure credential storage with encryption."""

import json
import os
import base64
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet


class CredentialStore:
    """Securely store and retrieve cloud credentials."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize credential store.

        Args:
            config_dir: Directory for storing credentials (defaults to ~/.cloud-automation)
        """
        if config_dir is None:
            self.config_dir = Path.home() / '.cloud-automation'
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_file = self.config_dir / 'credentials.enc'
        self._cipher = self._get_cipher()

    def _get_cipher(self) -> Fernet:
        """Get encryption cipher using machine-specific key.

        Returns:
            Fernet cipher instance
        """
        # Create a key based on username and hostname (machine-specific)
        import socket
        import getpass

        try:
            username = getpass.getuser()
            hostname = socket.gethostname()
        except Exception:
            # Fallback if we can't get user/hostname
            username = "default"
            hostname = "localhost"

        # Derive a key from username and hostname
        key_material = f"{username}@{hostname}".encode()
        key_hash = hashlib.sha256(key_material).digest()
        key = base64.urlsafe_b64encode(key_hash)

        return Fernet(key)

    def save_credentials(self, credentials: Dict[str, Any]) -> None:
        """Save credentials to encrypted file.

        Args:
            credentials: Dictionary containing credentials
        """
        try:
            # Convert to JSON
            json_data = json.dumps(credentials)

            # Encrypt
            encrypted_data = self._cipher.encrypt(json_data.encode())

            # Write to file with restrictive permissions
            self.credentials_file.write_bytes(encrypted_data)

            # Set file permissions to user read/write only (0600)
            os.chmod(self.credentials_file, 0o600)

        except Exception as e:
            raise RuntimeError(f"Failed to save credentials: {e}")

    def load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load credentials from encrypted file.

        Returns:
            Dictionary containing credentials, or None if file doesn't exist
        """
        if not self.credentials_file.exists():
            return None

        try:
            # Read encrypted data
            encrypted_data = self.credentials_file.read_bytes()

            # Decrypt
            decrypted_data = self._cipher.decrypt(encrypted_data)

            # Parse JSON
            credentials = json.loads(decrypted_data.decode())

            return credentials

        except Exception as e:
            # If decryption fails, the key might have changed (different machine)
            # or the file is corrupted
            raise RuntimeError(f"Failed to load credentials: {e}")

    def delete_credentials(self) -> None:
        """Delete stored credentials file."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()

    def credentials_exist(self) -> bool:
        """Check if credentials file exists.

        Returns:
            True if credentials are stored, False otherwise
        """
        return self.credentials_file.exists()

    def get_aws_credentials(self) -> Optional[Dict[str, str]]:
        """Get AWS credentials from store.

        Returns:
            Dictionary with AWS credentials or None
        """
        creds = self.load_credentials()
        if creds and 'aws_credentials' in creds:
            return creds['aws_credentials']
        return None

    def get_gcp_credentials(self) -> Optional[Dict[str, Any]]:
        """Get GCP credentials from store.

        Returns:
            Dictionary with GCP credentials or None
        """
        creds = self.load_credentials()
        if creds and 'gcp_credentials' in creds:
            return creds['gcp_credentials']
        return None

    def save_aws_credentials(self, aws_creds: Dict[str, str]) -> None:
        """Save AWS credentials.

        Args:
            aws_creds: AWS credentials dictionary
        """
        creds = self.load_credentials() or {}
        creds['aws_credentials'] = aws_creds
        self.save_credentials(creds)

    def save_gcp_credentials(self, gcp_creds: Dict[str, Any]) -> None:
        """Save GCP credentials.

        Args:
            gcp_creds: GCP credentials dictionary
        """
        creds = self.load_credentials() or {}
        creds['gcp_credentials'] = gcp_creds
        self.save_credentials(creds)
