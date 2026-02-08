import base64
import os
import hashlib

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class APIKeyCrypto:
    def __init__(self, password: str, salt: bytes = None):
        """
        Initialize the crypto handler with a password.

        Args:
            password (str): Mater password for encryption/decryption.
            salt (bytes, optional): If None, random salt will be generated.
        """

        if salt is None:
            self.salt = os.urandom(16)
        else:
            self.salt = salt

        # Derive key from password using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> dict:
        """
        Encrypt data using Fernet cipher.

        Args:
            data (str): Data to encrypt.

        Returns:
            dict: Contains encrypted data and salt (both base64 encoded).
        """
        encrypted_data = self.cipher.encrypt(data.encode())
        return {
            "data": base64.b64encode(encrypted_data).decode(),
            "salt": base64.b64encode(self.salt).decode(),
        }

    def decrypt(self, data: dict) -> str:
        """
        Decrypt data using Fernet cipher.

        Args:
            data (dict): Contains encrypted data and salt (both base64 encoded).

        Returns:
            str: Decrypted data.
        """
        encrypted_data = base64.b64decode(data["data"])
        decrypted_data = self.cipher.decrypt(encrypted_data)

        return decrypted_data.decode()


def encrypt_data(data: str, password: str) -> dict:
    """
    Encrypt data using Fernet cipher.

    Args:
        data (str): Data to encrypt.
        password (str): Master password for encryption/decryption.

    Returns:
        dict: Contains encrypted data and salt (both base64 encoded).
    """
    return APIKeyCrypto(password).encrypt(data)


def decrypt_data(data: dict, password: str) -> str:
    """
    Decrypt data using Fernet cipher.

    Args:
        data (dict): Contains encrypted data and salt (both base64 encoded).
        password (str): Master password for encryption/decryption.

    Returns:
        str: Decrypted data.
    """
    salt = base64.b64decode(data["salt"])
    return APIKeyCrypto(password, salt).decrypt(data)


def hash_key(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()
