"""The TCP client: sends one message to the server over TLS and receives its JSON response."""

import socket
import ssl

from shared.address import format_address
from shared.json_serialization import from_json
from shared.message_framing import MessageDecoder, encode_message
from shared.settings import (
    CLIENT_CONNECTION_TIMEOUT_SECONDS,
    CLIENT_RECEIVE_BUFFER_BYTES,
    CLIENT_RESPONSE_TIMEOUT_SECONDS,
    SERVER_PORT,
)
from tls.settings import TLS_SERVER_NAME


def send_request(server_host: str, message: str, tls_context: ssl.SSLContext):
    """Connects, verifies the server, sends one message, and returns the JSON response."""
    encoded_message = encode_message(message)
    with socket.create_connection(
        (server_host, SERVER_PORT), timeout=CLIENT_CONNECTION_TIMEOUT_SECONDS
    ) as plain_socket:
        # The certificate is issued to a fixed name, so it stays valid if the server's IP changes.
        with tls_context.wrap_socket(plain_socket, server_hostname=TLS_SERVER_NAME) as server_socket:
            print(f"Connected securely to {format_address(server_host, SERVER_PORT)} using {server_socket.version()}")
            server_socket.sendall(encoded_message)
            print(f"Sent: {message}")

            server_socket.settimeout(CLIENT_RESPONSE_TIMEOUT_SECONDS)
            return _receive_response(server_socket)


def _receive_response(server_socket: ssl.SSLSocket):
    message_decoder = MessageDecoder()
    while data := server_socket.recv(CLIENT_RECEIVE_BUFFER_BYTES):
        for response in message_decoder.decode(data):
            return from_json(response)
    raise ConnectionError("The server closed the connection before sending a complete response")
