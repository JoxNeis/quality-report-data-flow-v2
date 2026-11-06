"""Starts the TCP server and keeps it running until Ctrl+C.

Usage: python src/run_server.py
"""

import time

from server.tcp_server import TcpServer
from shared.settings import (
    SERVER_KEEP_ALIVE_INTERVAL_SECONDS,
    SERVER_LISTEN_HOST,
    SERVER_PORT,
)


def main():
    server = TcpServer(SERVER_LISTEN_HOST, SERVER_PORT)
    server.start()

    # Keep the main thread alive and free while the background threads do the work.
    try:
        while True:
            time.sleep(SERVER_KEEP_ALIVE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        server.stop()


if __name__ == "__main__":
    main()
