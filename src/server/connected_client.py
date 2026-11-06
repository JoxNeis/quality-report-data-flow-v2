"""The data the server keeps for one connected client."""

import ssl
import threading
from dataclasses import dataclass, field


@dataclass
class ConnectedClient:
    """Everything the server keeps for one connected client."""
    address: str
    client_socket: ssl.SSLSocket
    watcher_thread: threading.Thread = field(init=False)
    is_secured: bool = False  # True once the TLS handshake has succeeded.
