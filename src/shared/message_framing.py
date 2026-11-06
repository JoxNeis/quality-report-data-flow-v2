"""Marks where each message starts and ends, because TCP is only a stream of bytes.

A single message can arrive in several pieces, and several messages can arrive together.
So each message is sent as a 4-byte length followed by its text.
"""

from collections.abc import Iterator

from shared.settings import MAX_MESSAGE_BYTES

LENGTH_PREFIX_BYTES = 4


def encode_message(message: str) -> bytes:
    """Returns the bytes to send for a message. Raises ValueError if it is too large."""
    payload = message.encode()
    _check_message_size(len(payload))
    return len(payload).to_bytes(LENGTH_PREFIX_BYTES, "big") + payload


class MessageDecoder:
    """Rebuilds whole messages from the pieces of data received from one client."""

    def __init__(self):
        self._buffer = bytearray()

    @property
    def has_incomplete_message(self) -> bool:
        return len(self._buffer) > 0

    def decode(self, data: bytes) -> Iterator[str]:
        """Yields each message completed by this data. Raises ValueError on an invalid message."""
        self._buffer.extend(data)
        while len(self._buffer) >= LENGTH_PREFIX_BYTES:
            payload_size = int.from_bytes(self._buffer[:LENGTH_PREFIX_BYTES], "big")
            _check_message_size(payload_size)

            message_end = LENGTH_PREFIX_BYTES + payload_size
            if len(self._buffer) < message_end:
                return  # The rest of this message hasn't arrived yet.

            payload = bytes(self._buffer[LENGTH_PREFIX_BYTES:message_end])
            del self._buffer[:message_end]
            yield payload.decode()


def _check_message_size(size: int):
    if size > MAX_MESSAGE_BYTES:
        raise ValueError(f"A message of {size} bytes is over the {MAX_MESSAGE_BYTES} byte limit")
