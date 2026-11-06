"""Encrypts the database password and saves it to .env. Run this on the server device.

If .env has no DB_ENCRYPTION_KEY yet, this creates one.

Usage: python src/encrypt_db_password.py
"""

import getpass
import sys

from managers.environment_manager import (
    ENV_DB_ENCRYPTION_KEY,
    ENV_DB_PASSWORD_ENCRYPTED,
    EnvironmentManager,
)
from security.password_cipher import PasswordCipher, PasswordEncryptionError


def read_password() -> str:
    """Asks for the password without showing it on screen or saving it in the shell history."""
    password = getpass.getpass("Database password: ")
    if password != getpass.getpass("Repeat the password: "):
        sys.exit("The passwords don't match, so nothing was changed.")
    return password


def get_or_create_key(environment: EnvironmentManager) -> str:
    key = environment.get(ENV_DB_ENCRYPTION_KEY)
    if key:
        return key

    key = PasswordCipher.generate_key()
    environment.set_value(ENV_DB_ENCRYPTION_KEY, key)
    print(f"Created a new {ENV_DB_ENCRYPTION_KEY} in {environment.env_file}")
    return key


def main():
    environment = EnvironmentManager()
    password = read_password()
    if not password:
        print("Note: the password is empty.")

    try:
        encrypted_password = PasswordCipher(get_or_create_key(environment)).encrypt(password)
    except PasswordEncryptionError as error:
        sys.exit(f"{error}. Check {ENV_DB_ENCRYPTION_KEY} in {environment.env_file}.")

    environment.set_value(ENV_DB_PASSWORD_ENCRYPTED, encrypted_password)
    print(f"Saved the encrypted password as {ENV_DB_PASSWORD_ENCRYPTED} in {environment.env_file}")


if __name__ == "__main__":
    main()
