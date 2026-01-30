from typing import Optional


class RID:
    """
    Resource ID.
    A handle used to identify resources in the RenderingServer without passing objects.
    """

    _next_id = 1

    def __init__(self, from_rid: Optional["RID"] = None):
        """
        Initialize an RID. If from_rid is provided, it performs a value copy.
        """
        if from_rid:
            self._id = from_rid._id
        else:
            self._id = RID._next_id
            RID._next_id += 1

    def is_valid(self) -> bool:
        return self._id > 0

    def get_id(self) -> int:
        return self._id

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        if isinstance(other, RID):
            return self._id == other._id
        return False

    def __bool__(self):
        return self._id > 0
