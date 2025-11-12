"""Secure credential storage with encryption."""

import json
import os
import base64
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialStore:
    """Securely store and retrieve cloud credentials."""

    # Format version for backward compatibility
    FORMAT_VERSION = 2  # Version 2 uses PBKDF2+salt

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
        self.salt_file = self.config_dir / 'salt'

    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create new one.

        Returns:
            32-byte salt
        """
        if self.salt_file.exists():
            return self.salt_file.read_bytes()
        else:
            # Generate cryptographically secure random salt
            salt = secrets.token_bytes(32)
            self.salt_file.write_bytes(salt)
            os.chmod(self.salt_file, 0o600)
            return salt

    def _get_cipher(self, salt: Optional[bytes] = None) -> Fernet:
        """Get encryption cipher using PBKDF2 key derivation.

        Args:
            salt: Optional salt bytes (will be loaded/generated if not provided)

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

        key_material = f"{username}@{hostname}".encode()

        # Use provided salt or load/create
        if salt is None:
            salt = self._get_or_create_salt()

        # Use PBKDF2 for secure key derivation (OWASP 2023 recommendation: 600,000 iterations)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_material))

        return Fernet(key)

    def _get_legacy_cipher(self) -> Fernet:
        """Get old-style cipher for backward compatibility.

        Returns:
            Fernet cipher instance using old SHA256 method
        """
        import socket
        import getpass

        try:
            username = getpass.getuser()
            hostname = socket.gethostname()
        except Exception:
            username = "default"
            hostname = "localhost"

        key_material = f"{username}@{hostname}".encode()
        key_hash = hashlib.sha256(key_material).digest()
        key = base64.urlsafe_b64encode(key_hash)

        return Fernet(key)

    def save_credentials(self, credentials: Dict[str, Any]) -> None:
        """Save credentials to encrypted file using PBKDF2.

        Args:
            credentials: Dictionary containing credentials
        """
        try:
            # Get or create salt
            salt = self._get_or_create_salt()

            # Get cipher with PBKDF2
            cipher = self._get_cipher(salt)

            # Prepare data with version marker
            data = {
                'version': self.FORMAT_VERSION,
                'credentials': credentials
            }
            json_data = json.dumps(data)

            # Encrypt
            encrypted_data = cipher.encrypt(json_data.encode())

            # Write to file with restrictive permissions
            self.credentials_file.write_bytes(encrypted_data)

            # Set file permissions to user read/write only (0600)
            os.chmod(self.credentials_file, 0o600)

        except Exception as e:
            raise RuntimeError(f"Failed to save credentials: {e}")

    def load_credentials(self) -> Optional[Dict[str, Any]]:
        """Load credentials from encrypted file with automatic migration.

        Returns:
            Dictionary containing credentials, or None if file doesn't exist
        """
        if not self.credentials_file.exists():
            return None

        try:
            # Read encrypted data
            encrypted_data = self.credentials_file.read_bytes()

            # Try new format first (with PBKDF2)
            if self.salt_file.exists():
                try:
                    cipher = self._get_cipher()
                    decrypted_data = cipher.decrypt(encrypted_data)
                    data = json.loads(decrypted_data.decode())

                    # Check for version marker
                    if isinstance(data, dict) and 'version' in data:
                        return data['credentials']
                    else:
                        # Old format data loaded with new cipher - shouldn't happen
                        return data
                except Exception:
                    # If new format fails, try legacy
                    pass

            # Try legacy format (old SHA256 method)
            try:
                legacy_cipher = self._get_legacy_cipher()
                decrypted_data = legacy_cipher.decrypt(encrypted_data)
                credentials = json.loads(decrypted_data.decode())

                # Automatic migration: re-save with new format
                print("Migrating credentials to new secure format...")
                self.save_credentials(credentials)
                print("Migration complete!")

                return credentials

            except Exception as legacy_error:
                # Both methods failed
                raise RuntimeError(
                    f"Failed to load credentials. "
                    f"File may be corrupted or from different machine. "
                    f"Error: {legacy_error}"
                )

        except Exception as e:
            # If decryption fails, the key might have changed (different machine)
            # or the file is corrupted
            raise RuntimeError(f"Failed to load credentials: {e}")

    def delete_credentials(self) -> None:
        """Delete stored credentials and salt files."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
        if self.salt_file.exists():
            self.salt_file.unlink()

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
