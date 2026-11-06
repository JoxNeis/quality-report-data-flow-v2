"""Keeps track of which clients are currently connected."""

import threading

from server.connected_client import ConnectedClient


class ClientRegistry:
    """Stores the connected clients. Safe to use from several threads at once."""
    def __init__(self):
        self._clients: dict[str, ConnectedClient] = {}
        self._lock = threading.Lock()

    def add(self, client: ConnectedClient):
        with self._lock:
            self._clients[client.address] = client

    def remove(self, address: str):
        with self._lock:
            del self._clients[address]

    def get_all(self) -> list[ConnectedClient]:
        # Returns a copy, so looping over it is safe while clients come and go.
        with self._lock:
            return list(self._clients.values())
