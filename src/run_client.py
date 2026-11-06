"""Runs the TCP client: connects to the server over TLS, sends a message, and exits.

Usage: python src/run_client.py [server-ip] [message]
"""

import sys

from client.tcp_client import send_message
from shared.address import format_address
from shared.settings import (
    CLIENT_DEFAULT_MESSAGE,
    CLIENT_DEFAULT_SERVER_HOST,
    SERVER_PORT,
)
from tls.contexts import create_client_tls_context
from tls.settings import TLS_CERTIFICATE_FILE


def get_server_host() -> str:
    """Returns the IP given on the command line, or the default if there is none."""
    return sys.argv[1] if len(sys.argv) > 1 else CLIENT_DEFAULT_SERVER_HOST


def get_message() -> str:
    """Returns the message given on the command line, or the default if there is none."""
    return sys.argv[2] if len(sys.argv) > 2 else CLIENT_DEFAULT_MESSAGE


def main():
    # Print any character safely, even if the output is redirected to a limited encoding.
    sys.stdout.reconfigure(errors="backslashreplace")

    try:
        tls_context = create_client_tls_context()
    except OSError as error:
        sys.exit(f"Could not load {TLS_CERTIFICATE_FILE}: {error}\nCopy server.crt from the server device.")

    server_host = get_server_host()
    message = get_message()
    try:
        send_message(server_host, message, tls_context)
    except ValueError as error:
        sys.exit(f"Could not send the message: {error}")
    except OSError as error:
        sys.exit(f"Could not send the message to {format_address(server_host, SERVER_PORT)}: {error}")

    print(f"Sent: {message}")
    print("Connection closed")


if __name__ == "__main__":
    main()
