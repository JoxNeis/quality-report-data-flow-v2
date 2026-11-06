"""The TCP client: connects to the server and receives one message."""

import socket

from shared.address import format_address
from shared.settings import (
    CLIENT_CONNECTION_TIMEOUT_SECONDS,
    RECEIVE_BUFFER_BYTES,
    SERVER_PORT,
)


def receive_message(server_host: str) -> str:
    """Connects to the server, waits for one message, and closes the connection."""
    with socket.create_connection(
        (server_host, SERVER_PORT), timeout=CLIENT_CONNECTION_TIMEOUT_SECONDS
    ) as server_socket:
        print(f"Connected to {format_address(server_host, SERVER_PORT)}")
        return server_socket.recv(RECEIVE_BUFFER_BYTES).decode()
