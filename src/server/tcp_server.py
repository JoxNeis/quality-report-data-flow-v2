"""The TCP server: accepts many clients at once and prints the messages they send."""

import socket
import ssl
import threading

from server.client_registry import ClientRegistry
from server.connected_client import ConnectedClient
from shared.address import format_address
from shared.message_framing import MessageDecoder
from shared.settings import SERVER_RECEIVE_BUFFER_BYTES, SERVER_SOCKET_TIMEOUT_SECONDS
from tls.settings import TLS_HANDSHAKE_TIMEOUT_SECONDS


class TcpServer:
    """Listens for clients and receives each one's messages, in the background, until it disconnects."""

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
    def connections(self) -> dict[str, ssl.SSLSocket]:
        """The clients that finished the TLS handshake, as {"host:port": socket}.

        Don't send through these sockets from another thread. Each client's thread is always
        reading from its socket, and a TLS socket can't safely be used by two threads at once.
        """
        return {
            client.address: client.client_socket
            for client in self._clients.get_all()
            if client.is_secured
        }

    # endregion

    # region CONSTRUCTOR
    def __init__(
        self,
        host: str,
        port: int,
        tls_context: ssl.SSLContext,
        timeout_seconds: float = SERVER_SOCKET_TIMEOUT_SECONDS,
        verbose: bool = True,
    ):
        self.host = host
        self.port = port

        self._tls_context = tls_context
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
            plain_socket, (client_host, client_port) = accepted
            self._add_client(plain_socket, format_address(client_host, client_port))

    def _add_client(self, plain_socket: socket.socket, address: str):
        try:
            # This only prepares TLS. The handshake runs in the client's own thread,
            # so a slow or invalid client can't stop other clients from connecting.
            tls_socket = self._tls_context.wrap_socket(
                plain_socket, server_side=True, do_handshake_on_connect=False
            )
        except OSError as error:
            plain_socket.close()
            self._log(f"Could not set up TLS for {address}: {error}")
            return

        client = ConnectedClient(address, tls_socket)
        client.watcher_thread = self._create_background_thread(self._watch_client, client)
        # Add the client first, so its thread can never try to remove it too early.
        self._clients.add(client)
        client.watcher_thread.start()

    # endregion

    # region WATCHING CLIENTS
    def _watch_client(self, client: ConnectedClient):
        """Runs in one thread per client. The thread ends when this function returns."""
        with client.client_socket:
            if self._complete_tls_handshake(client):
                self._log(f"Client connected from {client.address} using {client.client_socket.version()}")
                self._receive_messages(client)
                self._log(f"Client disconnected from {client.address}")

        self._clients.remove(client.address)

    def _complete_tls_handshake(self, client: ConnectedClient) -> bool:
        """Returns whether the client completed the TLS handshake in time."""
        try:
            client.client_socket.settimeout(TLS_HANDSHAKE_TIMEOUT_SECONDS)
            client.client_socket.do_handshake()
            client.client_socket.settimeout(self._timeout_seconds)
        except OSError as error:
            self._log(f"TLS handshake failed for {client.address}: {error}")
            return False

        client.is_secured = True
        return True

    def _receive_messages(self, client: ConnectedClient):
        """Prints each message from the client, until it disconnects or the server stops."""
        message_decoder = MessageDecoder()
        receive_data = lambda: client.client_socket.recv(SERVER_RECEIVE_BUFFER_BYTES)
        try:
            # Empty data means the client closed the connection; None means the server stopped.
            while data := self._retry_until_stopped(receive_data):
                for message in message_decoder.decode(data):
                    # !r shows line breaks and control characters as text, so a client
                    # can't make its message look like one of the server's own status lines.
                    self._log(f"Message received from {client.address}: {message!r}")
        except ValueError as error:
            self._log(f"Invalid message from {client.address}: {error}")
            return
        except OSError:
            pass  # The connection was lost or closed.

        if message_decoder.has_incomplete_message:
            self._log(f"Connection from {client.address} ended in the middle of a message")

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
