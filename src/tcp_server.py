"""TCP demo server: waits for one client, sends it a message, closes, and exits.

Usage: python src/tcp_server.py
"""

import socket

PORT = 9000
MESSAGE = "Hello from the server!"

# 0.0.0.0 listens on all network interfaces, so other devices can connect.
with socket.create_server(("0.0.0.0", PORT)) as server:
    print(f"Waiting for a client on port {PORT} (Ctrl+C to stop)...")

    # Windows can't interrupt a blocking accept, so wake up regularly to let Ctrl+C through.
    server.settimeout(1)
    while True:
        try:
            conn, address = server.accept()
            break
        except TimeoutError:
            continue

    with conn:
        print(f"Client connected from {address[0]}:{address[1]}")
        conn.sendall(MESSAGE.encode())
        print(f"Sent: {MESSAGE}")

print("Connection closed")
