"""Checks whether the TLS certificate and private key exist, and creates them if needed."""

import shutil
import subprocess

from tls.settings import (
    TLS_CERTIFICATE_FILE,
    TLS_CERTIFICATE_VALID_DAYS,
    TLS_CERTIFICATES_FOLDER,
    TLS_PRIVATE_KEY_FILE,
    TLS_SERVER_NAME,
)


class TlsSetupError(Exception):
    """TLS could not be set up. The message explains what to do."""


def is_tls_set_up() -> bool:
    return TLS_CERTIFICATE_FILE.exists() and TLS_PRIVATE_KEY_FILE.exists()


def set_up_tls():
    """Creates the certificate and private key. Never replaces an existing file."""
    # Replacing a key would make clients stop trusting the server, so that stays the user's decision.
    if TLS_CERTIFICATE_FILE.exists() or TLS_PRIVATE_KEY_FILE.exists():
        raise TlsSetupError(
            f"{TLS_CERTIFICATES_FOLDER} has only one of {TLS_CERTIFICATE_FILE.name} and "
            f"{TLS_PRIVATE_KEY_FILE.name}. Restore the missing file, or delete both to create new ones."
        )

    openssl_path = shutil.which("openssl")
    if not openssl_path:
        raise TlsSetupError("The openssl command was not found. Install OpenSSL, or Git for Windows, which includes it.")

    TLS_CERTIFICATES_FOLDER.mkdir(exist_ok=True)
    result = subprocess.run(_build_openssl_command(openssl_path), capture_output=True, text=True)
    if result.returncode != 0:
        # Remove anything half-created, so the next run can start clean.
        TLS_CERTIFICATE_FILE.unlink(missing_ok=True)
        TLS_PRIVATE_KEY_FILE.unlink(missing_ok=True)
        raise TlsSetupError(f"openssl failed:\n{result.stderr}")


def _build_openssl_command(openssl_path: str) -> list[str]:
    return [
        openssl_path, "req", "-x509", "-noenc",
        "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
        "-keyout", str(TLS_PRIVATE_KEY_FILE),
        "-out", str(TLS_CERTIFICATE_FILE),
        "-days", str(TLS_CERTIFICATE_VALID_DAYS),
        "-subj", f"/CN={TLS_SERVER_NAME}",
        "-addext", f"subjectAltName=DNS:{TLS_SERVER_NAME}",
        "-addext", "basicConstraints=critical,CA:TRUE,pathlen:0",
        "-addext", "keyUsage=critical,digitalSignature,keyCertSign",
    ]
