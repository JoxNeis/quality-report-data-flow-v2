"""Helper for writing network addresses."""


def format_address(host: str, port: int) -> str:
    """Returns an address written as "host:port"."""
    return f"{host}:{port}"
