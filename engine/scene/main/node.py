import fnmatch
from typing import List, Optional, TYPE_CHECKING
from engine.core.object import Object
from engine.logger import Logger

if TYPE_CHECKING:
    from engine.scene.main.scene_tree import SceneTree
    from engine.scene.main.viewport import Viewport


class Node(Object):
    """
    Base class for all scene objects.
    """

    NOTIFICATION_ENTER_TREE = 10
    NOTIFICATION_EXIT_TREE = 11
    NOTIFICATION_READY = 13
    NOTIFICATION_PAUSED = 14
    NOTIFICATION_UNPAUSED = 15

    def __init__(self, name: str = "Node"):
        super().__init__()
        self.name: str = name
        self.parent: Optional["Node"] = None
        self.children: List["Node"] = []
        self._groups: set[str] = set()
        self._is_ready: bool = False
        self._tree: Optional["SceneTree"] = None  # noqa: F821
        self._queued_for_deletion: bool = False
        self._owner: Optional["Node"] = None

    def _notification(self, what: int) -> None:
        """
        Handle Node-specific notifications.
        """
        super()._notification(what)

    @property
    def owner(self) -> Optional["Node"]:
        """
        The node that owns this node. Used for serialization and find_child filtering.
        """
        return self._owner

    @owner.setter
    def owner(self, value: Optional["Node"]):
        """
        Sets the owner of the node. The owner must be an ancestor of this node
        in the scene tree, though this implementation allows flexible assignment
        for runtime generation logic.
        """
        self._owner = value

    def is_inside_tree(self) -> bool:
        """
        Returns True if this node is currently inside a SceneTree.
        """
        return self._tree is not None

    def to_string(self) -> str:
        return f"<{self._class_name}:{self.name}#{self._instance_id}>"

    @property
    def tree(self):
        return self._tree

    @tree.setter
    def tree(self, value):
        self._tree = value
        for child in self.children:
            child.tree = value

    def add_child(self, node: "Node"):
        """Adds a child. If the tree is active, triggers entry notifications correctly."""
        if node.parent is not None:
            raise ValueError(f"Node '{node.name}' already has a parent.")

        node.parent = self
        self.children.append(node)

        if self._tree:
            node._set_tree(self._tree)
            node._propagate_enter_tree()
            node._propagate_ready()

    def _set_tree(self, tree):
        self._tree = tree
        for child in self.children:
            child._set_tree(tree)

    def queue_free(self):
        """
        Queues this node for deletion at the end of the current frame.
        """
        if self._queued_for_deletion:
            return

        self._queued_for_deletion = True
        if self._tree:
            self._tree.queue_delete(self)
        else:
            Logger.warn(
                f"Node {self.name} called queue_free() but is not in the scene tree. It will not be deleted automatically.",
                "Node",
            )

    def is_queued_for_deletion(self) -> bool:
        return self._queued_for_deletion

    def find_child(
        self, pattern: str, recursive: bool = True, owned: bool = True
    ) -> Optional["Node"]:
        """
        Finds the first child node that matches the given pattern.

        Args:
            pattern: The name pattern to match (supports wildcards * and ?).
            recursive: If True, searches children recursively (Depth First).
            owned: If True, only searches nodes where node.owner == self.
        """
        for child in self.children:
            if owned and child.owner != self:
                continue

            if fnmatch.fnmatch(child.name, pattern):
                return child

        if recursive:
            for child in self.children:
                result = child.find_child(pattern, recursive, owned)
                if result:
                    return result

        return None

    def find_children(
        self,
        pattern: str,
        type_name: str = "",
        recursive: bool = True,
        owned: bool = True,
    ) -> List["Node"]:
        """
        Finds all child nodes that match the given pattern and optional type.

        Args:
            pattern: The name pattern to match (supports wildcards * and ?).
            type_name: Filter by class name (string). Empty string matches all.
            recursive: If True, searches children recursively.
            owned: If True, only collects nodes where node.owner == self.
        """
        results: List["Node"] = []

        for child in self.children:
            match_name = fnmatch.fnmatch(child.name, pattern)
            match_owner = (not owned) or (child.owner == self)
            match_type = (type_name == "") or child.is_class(type_name)

            if match_name and match_owner and match_type:
                results.append(child)

            if recursive:
                results.extend(
                    child.find_children(pattern, type_name, recursive, owned)
                )

        return results

    def _propagate_enter_tree(self):
        """Recursively notifies entry (Pre-Order: Parent -> Child)"""
        self.notification(self.NOTIFICATION_ENTER_TREE)
        self._enter_tree()
        for child in self.children:
            child._propagate_enter_tree()

    def _propagate_ready(self):
        """Recursively triggers ready (Post-Order: Child -> Parent)"""
        if self._is_ready:
            return

        for child in list(self.children):
            if not child._is_ready:
                child._propagate_ready()

        self.notification(self.NOTIFICATION_READY)
        self._ready()
        self._is_ready = True

    def _ready(self):
        """Called once when the node enters the scene tree."""
        pass

    def _enter_tree(self):
        """Called when the node enters the scene tree (before _ready)."""
        if self._tree:
            for group in self._groups:
                self._tree._add_node_to_group(self, group)

    def _exit_tree(self):
        """Called when the node is removed from the scene tree."""
        if self._tree:
            for group in self._groups:
                self._tree._remove_node_from_group(self, group)

    def remove_child(self, node: "Node"):
        if node in self.children:
            if self._tree:
                node._propagate_exit_tree()

            self.children.remove(node)
            node.parent = None

    def _propagate_exit_tree(self):
        """
        Recursively notifies children they are exiting the tree (Post-Order).
        """
        for child in list(self.children):
            child._propagate_exit_tree()

        self.notification(self.NOTIFICATION_EXIT_TREE)
        self._exit_tree()

        self._tree = None
        self._is_ready = False

    def _process(self, delta: float):
        """Called every frame."""
        pass

    def _input(self, _event) -> bool:
        """
        Called when there is an input event. The input event propagates down the node tree
        until a node consumes it.
        Override this in subclasses.
        """
        _ = self
        return False

    def _unhandled_input(self, _event) -> bool:
        """
        Called when an InputEvent hasn't been consumed by _input or any GUI Control item.
        Used for gameplay.
        Override this in subclasses.
        """
        _ = self
        return False

    def _unhandled_key_input(self, _event) -> bool:
        """
        Called when an InputEventKey hasn't been consumed by _input or any GUI Control item.
        Override this in subclasses.
        """
        _ = self
        return False

    def get_path(self) -> str:
        """
        Returns the absolute path to this node from the root.
        """
        if self.parent is None:
            return "/root"

        path_components = [self.name]
        current = self.parent
        while current is not None:
            if current.parent is None:
                path_components.append("root")
                path_components.append("")
            else:
                path_components.append(current.name)
            current = current.parent

        return "/".join(reversed(path_components))

    def get_node(self, path: str) -> Optional["Node"]:
        if not path:
            return None

        current: Optional["Node"] = self
        if path.startswith("/root"):
            while current and current.parent is not None:
                current = current.parent
            path = path[5:]
            if path.startswith("/"):
                path = path[1:]

        if not path:
            return current

        parts = path.split("/")
        for part in parts:
            if current is None:
                return None

            if part == "." or part == "":
                continue
            elif part == "..":
                current = current.parent
            else:
                found = False
                for child in current.children:
                    if child.name == part:
                        current = child
                        found = True
                        break
                if not found:
                    return None

        return current

    def get_path_to(self, target: "Node") -> str:
        """
        Returns the relative path from this node to the target node.

        Args:
            target: The target node to create a path to

        Returns:
            str: A relative NodePath that can be used with get_node()

        Example:
            If self is at /root/Game/PlayerBoard/Slot_0_0
            And target is at /root/Game/EnemyBoard/Slot_1_0
            Returns: "../../EnemyBoard/Slot_1_0"
        """
        if target is None:
            return ""

        self_path = self.get_path()
        target_path = target.get_path()
        self_parts = [p for p in self_path.split("/") if p]
        target_parts = [p for p in target_path.split("/") if p]
        common_depth = 0
        for i in range(min(len(self_parts), len(target_parts))):
            if self_parts[i] == target_parts[i]:
                common_depth = i + 1
            else:
                break

        levels_up = len(self_parts) - common_depth
        path_parts = [".."] * levels_up
        path_parts.extend(target_parts[common_depth:])
        return "/".join(path_parts) if path_parts else "."

    def get_viewport(self) -> Optional["Viewport"]:
        if self.get_class() == "Viewport":
            return self  # type: ignore

        if self.parent:
            return self.parent.get_viewport()

        return None

    def get_parent(self) -> Optional["Node"]:
        return self.parent

    def get_children(self) -> List["Node"]:
        """
        Returns a list of the node's children.
        Returns a shallow copy to allow safe iteration while modifying the tree.
        """
        return list(self.children)

    def add_to_group(self, group: str, persistent: bool = False):
        self._groups.add(group)
        if self._tree:
            self._tree._add_node_to_group(self, group)

    def remove_from_group(self, group: str):
        if group in self._groups:
            self._groups.remove(group)
            if self._tree:
                self._tree._remove_node_from_group(self, group)

    def is_in_group(self, group: str) -> bool:
        return group in self._groups

    def get_tree(self) -> Optional["SceneTree"]:
        return self._tree
