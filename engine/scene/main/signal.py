from typing import Callable, List
from engine.logger import Logger


class Signal:
    """
    Allows objects to broadcast events to connected listeners.
    """

    def __init__(self, name: str = "Signal"):
        self.name = name
        self._listeners: List[Callable] = []

    def connect(self, callback: Callable):
        """Connects a callback function to this signal."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def disconnect(self, callback: Callable):
        """Removes a callback function from this signal."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, *args, **kwargs):
        """Triggers all connected callbacks with the provided arguments."""
        for callback in self._listeners:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                Logger.error(f"Signal '{self.name}' emit failed: {e}", "Signal")

    def is_connected(self, callback: Callable) -> bool:
        """
        Checks if a callback is already connected to this signal.

        Args:
            callback: The callable to check

        Returns:
            True if the callback is connected, False otherwise
        """
        return callback in self._listeners

    def get_connections(self) -> List[Callable]:
        """
        Returns a copy of all connected callbacks.

        Returns:
            List of all connected callable objects
        """
        return self._listeners.copy()

    def is_null(self) -> bool:
        """
        Checks if the signal has no connections.

        Returns:
            True if no callbacks are connected, False otherwise
        """
        return len(self._listeners) == 0

    def get_connection_count(self) -> int:
        """
        Returns the number of connected callbacks.

        Returns:
            Number of connections
        """
        return len(self._listeners)
