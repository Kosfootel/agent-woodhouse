"""
Encryption utilities for Vigil

Uses Fernet symmetric encryption for storing sensitive data
like router passwords.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _get_key() -> bytes:
    """
    Get or generate encryption key.
    Uses VIGIL_KEY environment variable or a fallback key.
    """
    key_env = os.getenv('VIGIL_KEY', 'fallback-key-32bytes-long!!!!!')
    
    # Fernet requires a 32-byte base64-encoded key
    # If the key is not already Fernet-formatted, derive it
    if len(key_env) == 32:
        # Pad or encode the key properly for Fernet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'vigil-static-salt-32bytes-long!',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_env.encode()))
    else:
        # Try to use as-is if it's base64
        try:
            # Check if it's a valid Fernet key
            decoded = base64.urlsafe_b64decode(key_env)
            if len(decoded) == 32:
                key = key_env.encode()
            else:
                # Derive from string
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'vigil-static-salt-32bytes-long!',
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(key_env.encode()))
        except Exception:
            # Derive from string
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'vigil-static-salt-32bytes-long!',
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key_env.encode()))
    
    return key


def encrypt_password(password: str) -> str:
    """
    Encrypt a password string.
    
    Args:
        password: The plain text password to encrypt
        
    Returns:
        Base64-encoded encrypted string
    """
    if not password:
        return ""
    
    key = _get_key()
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt an encrypted password string.
    
    Args:
        encrypted_password: The encrypted password from encrypt_password()
        
    Returns:
        The original plain text password
    """
    if not encrypted_password:
        return ""
    
    try:
        key = _get_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception:
        # If decryption fails, return empty string
        return ""


# Convenience function for testing
if __name__ == "__main__":
    test_password = "my_secret_password"
    encrypted = encrypt_password(test_password)
    print(f"Original: {test_password}")
    print(f"Encrypted: {encrypted}")
    
    decrypted = decrypt_password(encrypted)
    print(f"Decrypted: {decrypted}")
    print(f"Match: {test_password == decrypted}")
