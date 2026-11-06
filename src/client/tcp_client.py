"""The TCP client: connects to the server over TLS and sends one message."""

import socket
import ssl

from shared.address import format_address
from shared.message_framing import encode_message
from shared.settings import CLIENT_CONNECTION_TIMEOUT_SECONDS, SERVER_PORT
from tls.settings import TLS_SERVER_NAME


def send_message(server_host: str, message: str, tls_context: ssl.SSLContext):
    """Connects to the server, verifies it, sends one message, and closes the connection."""
    encoded_message = encode_message(message)
    with socket.create_connection(
        (server_host, SERVER_PORT), timeout=CLIENT_CONNECTION_TIMEOUT_SECONDS
    ) as plain_socket:
        # The certificate is issued to a fixed name, so it stays valid if the server's IP changes.
        with tls_context.wrap_socket(plain_socket, server_hostname=TLS_SERVER_NAME) as server_socket:
            print(f"Connected securely to {format_address(server_host, SERVER_PORT)} using {server_socket.version()}")
            server_socket.sendall(encoded_message)
