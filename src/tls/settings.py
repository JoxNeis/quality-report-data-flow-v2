"""All TLS settings, in one place."""

from pathlib import Path

TLS_CERTIFICATES_FOLDER = Path(__file__).resolve().parents[2] / "certs"
TLS_CERTIFICATE_FILE = TLS_CERTIFICATES_FOLDER / "server.crt"  # Public: needed on both devices.
TLS_PRIVATE_KEY_FILE = TLS_CERTIFICATES_FOLDER / "server.key"  # Secret: server device only.
TLS_SERVER_NAME = "quality-report-server"  # The client checks the certificate is for this name.
TLS_CERTIFICATE_VALID_DAYS = 365
TLS_HANDSHAKE_TIMEOUT_SECONDS = 5  # The server drops a client that takes longer than this.
