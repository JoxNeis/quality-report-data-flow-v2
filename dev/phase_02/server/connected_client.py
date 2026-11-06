"""The data the server keeps for one connected client."""

import socket
import threading
from dataclasses import dataclass


@dataclass
class ConnectedClient:
    """Everything the server keeps for one connected client."""
    address: str
    client_socket: socket.socket
    watcher_thread: threading.Thread
