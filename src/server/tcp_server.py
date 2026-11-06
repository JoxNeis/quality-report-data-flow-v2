"""The TCP server: accepts many clients at once and tracks them until they disconnect."""

import socket
import threading

from server.client_registry import ClientRegistry
from server.connected_client import ConnectedClient
from shared.address import format_address
from shared.settings import RECEIVE_BUFFER_BYTES, SERVER_SOCKET_TIMEOUT_SECONDS


class TcpServer:
    """Listens for clients and watches each one, in the background, until it disconnects."""

    # region PROPERTIES
    @property
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, value: str):
        if not value:
            raise ValueError("TcpServer.EmptyHost")
        self._host = value

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int):
        if value < 0:
            raise ValueError("TcpServer.NegativePort")
        self._port = value

    @property
    def connections(self) -> dict[str, socket.socket]:
        """The connected clients, as {"host:port": socket}."""
        return {
            client.address: client.client_socket for client in self._clients.get_all()
        }

    # endregion

    # region CONSTRUCTOR
    def __init__(
        self,
        host: str,
        port: int,
        timeout_seconds: float = SERVER_SOCKET_TIMEOUT_SECONDS,
        verbose: bool = True,
    ):
        self.host = host
        self.port = port

        self._timeout_seconds = timeout_seconds
        self._verbose = verbose
        self._clients = ClientRegistry()
        self._stop_requested = threading.Event()

    # endregion

    # region START AND STOP
    def start(self):
        """Opens the listening socket and starts accepting clients in the background."""
        self._listening_socket = socket.create_server((self.host, self.port))
        self._listening_socket.settimeout(self._timeout_seconds)
        self._log("Server Started")

        self._log(f"Server is listening in {format_address(self.host, self.port)}")
        self._accept_thread = self._create_background_thread(self._accept_clients)
        self._accept_thread.start()

    def stop(self):
        """Stops accepting clients, disconnects the current ones, and closes the server."""
        self._stop_requested.set()
        self._accept_thread.join()

        # Each watcher thread closes its own socket and removes its own client as it ends.
        for client in self._clients.get_all():
            client.watcher_thread.join()

        self._listening_socket.close()
        self._log("Server Stopped")

    # endregion

    # region ACCEPTING CLIENTS
    def _accept_clients(self):
        """Runs in the accept thread, adding each new client until the server stops."""
        while accepted := self._retry_until_stopped(self._listening_socket.accept):
            client_socket, (client_host, client_port) = accepted
            self._add_client(client_socket, format_address(client_host, client_port))

    def _add_client(self, client_socket: socket.socket, address: str):
        client_socket.settimeout(self._timeout_seconds)
        watcher_thread = self._create_background_thread(
            self._watch_client, client_socket, address
        )
        # Add the client first, so its thread can never try to remove it too early.
        self._clients.add(ConnectedClient(address, client_socket, watcher_thread))
        self._log(f"Client connected from {address}")
        watcher_thread.start()

    # endregion

    # region WATCHING CLIENTS
    def _watch_client(self, client_socket: socket.socket, address: str):
        """Runs in one thread per client. The thread ends when this function returns."""
        with client_socket:
            self._wait_until_disconnected(client_socket)

        self._clients.remove(address)
        self._log(f"Client disconnected from {address}")

    def _wait_until_disconnected(self, client_socket: socket.socket):
        """Returns once the connection closes or the server stops. Discards received data."""
        receive_data = lambda: client_socket.recv(RECEIVE_BUFFER_BYTES)
        try:
            # Empty data means the client closed the connection; None means the server stopped.
            while self._retry_until_stopped(receive_data):
                pass
        except OSError:
            pass  # The connection was lost or closed.

    # endregion

    # region HELPERS
    def _retry_until_stopped(self, socket_call):
        """Repeats a socket call each time it times out. Returns None if the server stops.

        Socket calls time out regularly so that waiting threads can notice stop().
        """
        while not self._stop_requested.is_set():
            try:
                return socket_call()
            except TimeoutError:
                continue
        return None

    def _create_background_thread(self, target, *args) -> threading.Thread:
        return threading.Thread(target=target, args=args, daemon=True)

    def _log(self, message: str):
        if self._verbose:
            print(message)

    # endregion
