"""TCP demo client: connects to the server, prints its message, and exits.

Usage: python src/tcp_client.py <server-ip>
"""

import socket
import sys

PORT = 9000

host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"

try:
    with socket.create_connection((host, PORT), timeout=5) as sock:
        print(f"Connected to {host}:{PORT}")
        print(f"Received: {sock.recv(1024).decode()}")
except OSError as error:
    sys.exit(f"Could not connect to {host}:{PORT}: {error}")

print("Connection closed")
