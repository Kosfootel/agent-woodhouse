"""Vigil Credential Vault - Encryption Service

Provides AES-256-GCM encryption for credential storage.
Uses environment variable for master key derivation.
"""

import os
import secrets
import hashlib
import logging
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("vigil.vault.encryption")


class VaultEncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""
    pass


class VaultEncryptionService:
    """AES-256-GCM encryption service for the credential vault.

    Uses a master key derived from environment variable VIGIL_VAULT_MASTER_KEY.
    Each credential is encrypted with a unique nonce.
    """

    KEY_SIZE = 32  # 256 bits
    NONCE_SIZE = 12  # 96 bits recommended for GCM
    SALT_SIZE = 16  # 128 bits
    PBKDF2_ITERATIONS = 100000

    def __init__(self, master_key: Optional[str] = None):
        """Initialize the encryption service.

        Args:
            master_key: Optional master key. If not provided, reads from
                       VIGIL_VAULT_MASTER_KEY environment variable.

        Raises:
            VaultEncryptionError: If no master key is provided or found.
        """
        key_source = master_key or os.environ.get("VIGIL_VAULT_MASTER_KEY")

        if not key_source:
            raise VaultEncryptionError(
                "VIGIL_VAULT_MASTER_KEY not set. "
                "Generate with: openssl rand -base64 32"
            )

        # Derive a fixed-size key from the master key
        self._master_key = key_source.encode("utf-8")
        self._derived_key = self._derive_key(self._master_key)

    def _derive_key(self, master_key: bytes) -> bytes:
        """Derive a 256-bit encryption key from master key using SHA-256.

        Uses a static salt based on application name for deterministic key derivation.
        This is acceptable because we use unique nonces per encryption operation.
        """
        # Use a static salt for key derivation - the security relies on
        # the master key entropy, not the salt
        static_salt = b"vigil-credential-vault-v1"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=static_salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=default_backend(),
        )
        return kdf.derive(master_key)

    def encrypt(self, plaintext: str) -> Tuple[bytes, bytes]:
        """Encrypt plaintext credential data.

        Args:
            plaintext: The credential data to encrypt.

        Returns:
            Tuple of (encrypted_data_with_nonce, associated_data)
            The encrypted_data_with_nonce includes the nonce prefix.

        Raises:
            VaultEncryptionError: If encryption fails.
        """
        try:
            # Generate a unique nonce for this encryption
            nonce = secrets.token_bytes(self.NONCE_SIZE)

            # Create AES-GCM cipher
            aesgcm = AESGCM(self._derived_key)

            # Encrypt the plaintext
            plaintext_bytes = plaintext.encode("utf-8")
            ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)

            # Prepend nonce to ciphertext for storage
            encrypted_data = nonce + ciphertext

            return encrypted_data

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise VaultEncryptionError(f"Failed to encrypt credential: {e}")

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt credential data.

        Args:
            encrypted_data: The encrypted data with nonce prefix.

        Returns:
            The decrypted plaintext credential.

        Raises:
            VaultEncryptionError: If decryption fails (invalid key, tampered data).
        """
        try:
            if len(encrypted_data) < self.NONCE_SIZE + 16:  # Minimum: nonce + 1 block + tag
                raise VaultEncryptionError("Invalid encrypted data length")

            # Extract nonce and ciphertext
            nonce = encrypted_data[:self.NONCE_SIZE]
            ciphertext = encrypted_data[self.NONCE_SIZE:]

            # Create AES-GCM cipher
            aesgcm = AESGCM(self._derived_key)

            # Decrypt
            plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise VaultEncryptionError(f"Failed to decrypt credential: {e}")

    def rotate_key(self, new_master_key: str) -> None:
        """Rotate to a new master key.

        Note: This requires re-encrypting all credentials. Use with caution.
        This method only updates the internal key; actual credential re-encryption
        must be handled by the caller.

        Args:
            new_master_key: The new master key to use.
        """
        self._master_key = new_master_key.encode("utf-8")
        self._derived_key = self._derive_key(self._master_key)
        logger.info("Master key rotation completed")

    @staticmethod
    def generate_master_key() -> str:
        """Generate a secure random master key.

        Returns:
            A base64-encoded 256-bit random key.
        """
        return secrets.token_urlsafe(32)


# Singleton instance for application-wide use
_encryption_service: Optional[VaultEncryptionService] = None


def get_encryption_service() -> VaultEncryptionService:
    """Get or create the singleton encryption service instance.

    Returns:
        VaultEncryptionService singleton.

    Raises:
        VaultEncryptionError: If initialization fails.
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = VaultEncryptionService()
    return _encryption_service


def reset_encryption_service() -> None:
    """Reset the singleton (mainly for testing)."""
    global _encryption_service
    _encryption_service = None
