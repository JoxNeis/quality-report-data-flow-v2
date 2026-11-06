"""Runs the TCP client: connects to the server, prints its message, and exits.

Usage: python src/run_client.py [server-ip]
"""

import sys

from client.tcp_client import receive_message
from shared.address import format_address
from shared.settings import CLIENT_DEFAULT_SERVER_HOST, SERVER_PORT


def get_server_host() -> str:
    """Returns the IP given on the command line, or the default if there is none."""
    return sys.argv[1] if len(sys.argv) > 1 else CLIENT_DEFAULT_SERVER_HOST


def main():
    server_host = get_server_host()
    try:
        message = receive_message(server_host)
    except OSError as error:
        sys.exit(f"Could not connect to {format_address(server_host, SERVER_PORT)}: {error}")

    print(f"Received: {message}")
    print("Connection closed")


if __name__ == "__main__":
    main()
