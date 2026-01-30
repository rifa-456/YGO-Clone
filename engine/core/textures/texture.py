from abc import ABC
from engine.core.resource import Resource
from engine.core.rid import RID


class Texture(Resource, ABC):
    """
    Abstract base class for all texture datatypes.
    """

    def __init__(self) -> None:
        super().__init__()

    def get_width(self) -> int:
        return 0

    def get_height(self) -> int:
        return 0

    def get_rid(self) -> RID:
        return self._rid