"""Settings for the TCP server and client. TLS settings are in tls/settings.py."""

# Used by both sides
SERVER_PORT = 5000
MAX_MESSAGE_BYTES = 1024 * 1024

# Server
SERVER_LISTEN_HOST = "0.0.0.0"  # Listens on all network interfaces, so other devices can connect.
SERVER_SOCKET_TIMEOUT_SECONDS = 1  # How often waiting threads check whether the server is stopping.
SERVER_KEEP_ALIVE_INTERVAL_SECONDS = 1
SERVER_RECEIVE_BUFFER_BYTES = 4096

# Client
CLIENT_DEFAULT_SERVER_HOST = "169.254.142.155"
CLIENT_DEFAULT_MESSAGE = "Hello from the client!"
CLIENT_CONNECTION_TIMEOUT_SECONDS = 5
