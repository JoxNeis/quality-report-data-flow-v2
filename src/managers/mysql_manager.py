"""Connects to MySQL and runs queries."""

from dataclasses import dataclass, field
from typing import Self

import mysql.connector

from managers.environment_manager import (
    ENV_DB_ENCRYPTION_KEY,
    ENV_DB_HOST,
    ENV_DB_NAME,
    ENV_DB_PASSWORD_ENCRYPTED,
    ENV_DB_PORT,
    ENV_DB_USER,
    EnvironmentManager,
)
from security.password_cipher import PasswordCipher
from shared.settings import MYSQL_CONNECTION_TIMEOUT_SECONDS, MYSQL_DEFAULT_PORT


@dataclass(frozen=True)
class MySqlSettings:
    """The details needed to connect. repr=False keeps the password out of logs."""

    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)

    @classmethod
    def from_environment(cls, environment: EnvironmentManager) -> Self:
        """Reads the settings from the environment and decrypts the password, if there is one."""
        return cls(
            host=environment.get_required(ENV_DB_HOST),
            port=environment.get_int(ENV_DB_PORT, MYSQL_DEFAULT_PORT),
            database=environment.get_required(ENV_DB_NAME),
            user=environment.get_required(ENV_DB_USER),
            password=cls._read_password(environment),
        )

    @staticmethod
    def _read_password(environment: EnvironmentManager) -> str:
        encrypted_password = environment.get(ENV_DB_PASSWORD_ENCRYPTED)
        if encrypted_password is None:
            return ""  # The database has no password, so no key is needed either.

        cipher = PasswordCipher(environment.get_required(ENV_DB_ENCRYPTION_KEY))
        return cipher.decrypt(encrypted_password)


class MySqlManager:
    """Runs queries on one MySQL connection. Create one for each thread, not a shared one.

    Use it in a with block, so the connection always gets closed:

        with MySqlManager.from_environment() as database:
            rows = database.fetch_all("SELECT * FROM reports WHERE id = %s", (report_id,))
    """

    def __init__(self, settings: MySqlSettings):
        self._settings = settings
        self._connection = None

    @classmethod
    def from_environment(cls, environment: EnvironmentManager | None = None) -> Self:
        return cls(MySqlSettings.from_environment(environment or EnvironmentManager()))

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, *exception_details):
        self.close()

    def connect(self):
        # With autocommit, each change saves immediately and each read sees the latest data.
        self._connection = mysql.connector.connect(
            host=self._settings.host,
            port=self._settings.port,
            database=self._settings.database,
            user=self._settings.user,
            password=self._settings.password,
            connection_timeout=MYSQL_CONNECTION_TIMEOUT_SECONDS,
            autocommit=True,
        )

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def fetch_all(self, query: str, parameters: tuple = ()) -> list[dict]:
        """Runs a SELECT and returns each row as a dictionary of column name to value.

        Always pass values through parameters, with %s in the query. Never build
        the query from outside values, because that allows SQL injection.
        """
        with self._get_connection().cursor(dictionary=True) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()

    def execute(self, query: str, parameters: tuple = ()) -> int:
        """Runs a change such as INSERT or UPDATE, and returns how many rows it affected."""
        with self._get_connection().cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.rowcount

    def _get_connection(self):
        if self._connection is None:
            raise RuntimeError("MySqlManager is not connected. Call connect() first.")
        return self._connection
