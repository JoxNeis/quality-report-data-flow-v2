"""Creates the TLS configuration used by each side of the connection."""

import ssl

from tls.settings import TLS_CERTIFICATE_FILE, TLS_PRIVATE_KEY_FILE


def create_server_tls_context() -> ssl.SSLContext:
    """Lets the server prove its identity, using its certificate and private key."""
    tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls_context.load_cert_chain(TLS_CERTIFICATE_FILE, TLS_PRIVATE_KEY_FILE)
    # Session tickets would only speed up reconnecting. A client that closes without reading
    # them can reset the connection, and the server can lose a message it was about to read.
    tls_context.num_tickets = 0
    return tls_context


def create_client_tls_context() -> ssl.SSLContext:
    """Makes the client trust only our own certificate, not the device's usual authorities."""
    return ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=TLS_CERTIFICATE_FILE)
