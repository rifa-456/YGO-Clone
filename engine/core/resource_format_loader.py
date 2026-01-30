from abc import ABC, abstractmethod
from typing import List, Any
from engine.core.resource import Resource


class ResourceFormatLoader(ABC):
    """
    Base class for loading resources.
    """

    @abstractmethod
    def get_recognized_extensions(self) -> List[str]:
        """Returns the list of file extensions this loader can handle."""
        pass

    @abstractmethod
    def handles_type(self, type_name: str) -> bool:
        """Returns True if this loader handles the given resource type."""
        pass

    @abstractmethod
    def get_resource_type(self, path: str) -> str:
        """Returns the resource type associated with the given path."""
        pass

    @abstractmethod
    def load(self, path: str, original_path: str = "") -> Resource:
        """Loads the resource from the filesystem."""
        pass
