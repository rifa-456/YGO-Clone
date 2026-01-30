from typing import Any, Dict, List


class Object:
    """
    Base class for all non-built-in datatypes.
    Provides identification, metadata, and the foundation for the notification system.
    """

    _next_instance_id: int = 0

    def __init__(self) -> None:
        Object._next_instance_id += 1
        self._instance_id: int = Object._next_instance_id
        self._metadata: Dict[str, Any] = {}
        self._class_name: str = self.__class__.__name__
        self._block_signals: bool = False

    def get_instance_id(self) -> int:
        """Returns the unique instance ID (memory address in Python)."""
        return self._instance_id

    def get_class(self) -> str:
        """Returns the class name as a string."""
        return self._class_name

    def is_class(self, class_name: str) -> bool:
        """
        Check inheritance by string name.
        """
        if self._class_name == class_name:
            return True

        for cls in self.__class__.__mro__:
            if cls.__name__ == class_name:
                return True
        return False

    def set_meta(self, name: str, value: Any) -> None:
        """Attach arbitrary metadata to the object."""
        self._metadata[name] = value

    def get_meta(self, name: str, default: Any = None) -> Any:
        """Retrieve metadata."""
        return self._metadata.get(name, default)

    def has_meta(self, name: str) -> bool:
        return name in self._metadata

    def remove_meta(self, name: str) -> None:
        if name in self._metadata:
            del self._metadata[name]

    def get_meta_list(self) -> List[str]:
        return list(self._metadata.keys())

    def notification(self, what: int) -> None:
        """
        Public notification dispatcher.
        Calls the virtual _notification() method.
        """
        self._notification(what)

    def _notification(self, what: int) -> None:
        """
        Virtual notification handler. Override in subclasses.
        """
        pass

    def to_string(self) -> str:
        return f"<{self._class_name}#{self._instance_id}>"

    def __repr__(self) -> str:
        return self.to_string()

    def __str__(self) -> str:
        return self.to_string()
