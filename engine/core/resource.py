from typing import TypeVar
from engine.core.object import Object
from engine.core.rid import RID

T = TypeVar("T", bound="Resource")


class Resource(Object):
    """
    Base class for all resources.
    Resources are data containers that are reference-counted (automatically in Python)
    and can be saved/loaded from disk.
    """

    def __init__(self) -> None:
        super().__init__()
        self._rid = RID()
        self.resource_path: str = ""
        self.resource_name: str = ""
        self.resource_local_to_scene: bool = False

    def take_over_path(self, path: str) -> None:
        """
        Sets the path of the resource.
        In a full engine, this would also update the ResourceLoader cache.
        """
        self.resource_path = path

    def get_rid(self) -> RID:
        """
        Returns the actual RID handle, not just an integer ID.
        """
        return self._rid

    def duplicate(self: T, subresources: bool = False) -> T:
        """
        Returns a copy of the resource.
        """
        new_resource = self.__class__()
        new_resource.resource_name = self.resource_name
        new_resource.resource_local_to_scene = self.resource_local_to_scene

        for key, value in self.__dict__.items():
            if key.startswith("_") or key == "resource_path":
                continue

            if isinstance(value, Resource):
                if subresources:
                    setattr(new_resource, key, value.duplicate(True))
                else:
                    setattr(new_resource, key, value)
            elif isinstance(value, (int, float, str, bool, tuple)):
                setattr(new_resource, key, value)
            elif isinstance(value, list):
                setattr(new_resource, key, value.copy())
            elif isinstance(value, dict):
                setattr(new_resource, key, value.copy())

        new_resource._duplicate(subresources)

        return new_resource

    def _duplicate(self, subresources: bool) -> None:
        """
        Virtual method. Override to copy custom data (e.g. pygame Surfaces).
        """
        pass
