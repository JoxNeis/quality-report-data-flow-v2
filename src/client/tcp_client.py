"""The TCP client: sends one message to the server over TLS and receives its JSON response."""

import socket
import ssl

from shared.address import format_address
from shared.json_serialization import from_json
from shared.message_framing import MessageDecoder, encode_message
from shared.settings import (
    CLIENT_BIND_IP,
    CLIENT_CONNECTION_TIMEOUT_SECONDS,
    CLIENT_RECEIVE_BUFFER_BYTES,
    CLIENT_RESPONSE_TIMEOUT_SECONDS,
    SERVER_PORT,
)
from tls.settings import TLS_SERVER_NAME


class ClientBindIpError(Exception):
    """CLIENT_BIND_IP can't be used on this device. The message explains what to do."""


def send_request(server_host: str, message: str, tls_context: ssl.SSLContext):
    """Connects, verifies the server, sends one message, and returns the JSON response."""
    encoded_message = encode_message(message)
    with socket.create_connection(
        (server_host, SERVER_PORT),
        timeout=CLIENT_CONNECTION_TIMEOUT_SECONDS,
        source_address=_get_source_address(),
    ) as plain_socket:
        # The certificate is issued to a fixed name, so it stays valid if the server's IP changes.
        with tls_context.wrap_socket(plain_socket, server_hostname=TLS_SERVER_NAME) as server_socket:
            local_ip = server_socket.getsockname()[0]
            print(
                f"Connected securely to {format_address(server_host, SERVER_PORT)} "
                f"from {local_ip} using {server_socket.version()}"
            )
            server_socket.sendall(encoded_message)
            print(f"Sent: {message}")

            server_socket.settimeout(CLIENT_RESPONSE_TIMEOUT_SECONDS)
            return _receive_response(server_socket)


def _get_source_address() -> tuple[str, int] | None:
    """Returns the local address to connect from, or None to let Windows choose."""
    if not CLIENT_BIND_IP:
        return None

    # Binding on its own first tells apart a wrong local IP from a failed connection.
    try:
        with socket.socket() as test_socket:
            test_socket.bind((CLIENT_BIND_IP, 0))
    except OSError as error:
        raise ClientBindIpError(
            f"CLIENT_BIND_IP is {CLIENT_BIND_IP}, but that IP can't be used on this device: {error}\n"
            "It may have changed. Run ipconfig, find this device's Ethernet IPv4 address, "
            "and update CLIENT_BIND_IP in .env."
        ) from error
    return (CLIENT_BIND_IP, 0)


def _receive_response(server_socket: ssl.SSLSocket):
    message_decoder = MessageDecoder()
    while data := server_socket.recv(CLIENT_RECEIVE_BUFFER_BYTES):
        for response in message_decoder.decode(data):
            return from_json(response)
    raise ConnectionError("The server closed the connection before sending a complete response")
