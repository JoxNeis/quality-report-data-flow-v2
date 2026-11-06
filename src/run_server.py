"""Starts the TCP server over TLS and keeps it running until Ctrl+C.

On the first run, this also sets up TLS by creating the certificate and private key.

Usage: python src/run_server.py
"""

import ssl
import sys
import time

from server.message_handler import handle_client_message, handle_response_sent
from server.tcp_server import TcpServer
from shared.settings import (
    SERVER_KEEP_ALIVE_INTERVAL_SECONDS,
    SERVER_LISTEN_HOST,
    SERVER_PORT,
)
from tls.certificate_setup import TlsSetupError, is_tls_set_up, set_up_tls
from tls.contexts import create_server_tls_context
from tls.settings import TLS_CERTIFICATE_FILE, TLS_CERTIFICATES_FOLDER, TLS_PRIVATE_KEY_FILE


def prepare_tls_context() -> ssl.SSLContext:
    """Returns the server's TLS configuration, setting up TLS first if it isn't set up yet."""
    if is_tls_set_up():
        print("TLS is already set up")
    else:
        print("TLS is not set up. Setting it up now...")
        set_up_tls()
        print(f"Created {TLS_CERTIFICATE_FILE} (copy this to each client device)")
        print(f"Created {TLS_PRIVATE_KEY_FILE} (keep this secret, on this device only)")

    return create_server_tls_context()


def main():
    # Print any character safely, even if the output is redirected to a limited encoding.
    sys.stdout.reconfigure(errors="backslashreplace")

    try:
        tls_context = prepare_tls_context()
    except TlsSetupError as error:
        sys.exit(f"Could not set up TLS: {error}")
    except OSError as error:
        sys.exit(
            f"Could not load the TLS certificate: {error}\n"
            f"If the files are damaged, delete {TLS_CERTIFICATES_FOLDER} and run this again. "
            "Then copy the new server.crt to each client device."
        )

    server = TcpServer(
        SERVER_LISTEN_HOST,
        SERVER_PORT,
        tls_context,
        handle_client_message,
        handle_response_sent,
    )
    server.start()

    # Keep the main thread alive and free while the background threads do the work.
    try:
        while True:
            time.sleep(SERVER_KEEP_ALIVE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
