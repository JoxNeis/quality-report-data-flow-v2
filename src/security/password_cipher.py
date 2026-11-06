"""Encrypts and decrypts passwords using a secret key."""

from cryptography.fernet import Fernet, InvalidToken


class PasswordEncryptionError(Exception):
    """A password could not be encrypted or decrypted. The message explains why."""


class PasswordCipher:
    """Encrypts passwords so they aren't stored as readable text."""

    def __init__(self, key: str):
        try:
            self._fernet = Fernet(key)
        except ValueError as error:
            raise PasswordEncryptionError("The encryption key is not valid") from error

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode()

    def encrypt(self, password: str) -> str:
        return self._fernet.encrypt(password.encode()).decode()

    def decrypt(self, encrypted_password: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_password.encode()).decode()
        except InvalidToken as error:
            raise PasswordEncryptionError(
                "The password could not be decrypted. It may have been encrypted with "
                "a different key, so encrypt it again using the current one."
            ) from error
