from collections import defaultdict
from typing import Set, List, Dict
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2
from engine.scene.main.node import Node
from engine.scene.main.viewport import Viewport
from engine.servers.rendering.rendering_server import RenderingServer
from engine.core.rid import RID
from engine.logger import Logger  # Added Import


class SceneTree:
    """
    Manages the hierarchy of nodes and orchestrates the Update/Draw loops.
    """

    def __init__(
        self, root_node: Node, display_window_size: Vector2 = Vector2(800, 600)
    ):
        Logger.info("Initializing SceneTree...", "SceneTree")
        self._layout_queue: Set[Node] = set()
        self._delete_queue: Set[Node] = set()
        self._group_map: Dict[str, List[Node]] = defaultdict(list)

        self._server = RenderingServer.get_singleton()

        self.root_viewport = Viewport(name="root")
        self.root_viewport.set_size(
            int(display_window_size.x), int(display_window_size.y)
        )

        self._root_viewport_rid = self.root_viewport.get_viewport_rid()
        Logger.info(f"Root Viewport RID: {self._root_viewport_rid}", "SceneTree")

        self._server.viewport_attach_to_screen(
            self._root_viewport_rid,
            Rect2(0, 0, display_window_size.x, display_window_size.y),
        )

        self.root = self.root_viewport
        self.current_scene = root_node
        self.root_viewport.add_child(self.current_scene)
        self.root_viewport.tree = self

        Logger.info("Propagating _enter_tree and _ready...", "SceneTree")
        self.root_viewport._propagate_enter_tree()
        self.root_viewport._propagate_ready()

        self.current_camera = None
        Logger.info("SceneTree Initialized.", "SceneTree")

    def get_root_viewport_rid(self) -> RID:
        return self._root_viewport_rid

    def process(self, delta: float):
        """
        Runs the logic processing (Node._process).
        """
        self._process_node(self.root, delta)
        self._flush_delete_queue()
        self._flush_layout_queue()

        if hasattr(self, "current_camera") and self.current_camera:
            pass

    def render(self):
        """
        Triggers the rendering of the scene.
        Called by Main Loop (DisplayServer).
        """
        self._server.viewport_draw(self._root_viewport_rid, 0.016)

    def _process_node(self, node: Node, delta: float):
        node._process(delta)
        for child in node.children:
            self._process_node(child, delta)

    def queue_delete(self, node: Node):
        self._delete_queue.add(node)

    def _flush_delete_queue(self):
        if not self._delete_queue:
            return
        to_delete = list(self._delete_queue)
        self._delete_queue.clear()
        for node in to_delete:
            if node.parent:
                node.parent.remove_child(node)
            node.parent = None
            node.tree = None

    def queue_layout_update(self, node: Node):
        self._layout_queue.add(node)

    def _flush_layout_queue(self):
        max_iterations = 100
        iteration = 0
        while self._layout_queue and iteration < max_iterations:
            dirty_nodes = list(self._layout_queue)
            self._layout_queue.clear()
            for node in dirty_nodes:
                if hasattr(node, "notification"):
                    node.notification(46)
            iteration += 1
        if self._layout_queue:
            self._layout_queue.clear()

    def _add_node_to_group(self, node: Node, group: str):
        if node not in self._group_map[group]:
            self._group_map[group].append(node)

    def _remove_node_from_group(self, node: Node, group: str):
        if group in self._group_map:
            if node in self._group_map[group]:
                self._group_map[group].remove(node)

    def call_group(self, group: str, method: str, *args, **kwargs):
        if group not in self._group_map:
            return
        for node in list(self._group_map[group]):
            if hasattr(node, method):
                func = getattr(node, method)
                if callable(func):
                    func(*args, **kwargs)

    def get_nodes_in_group(self, group: str) -> List[Node]:
        return list(self._group_map.get(group, []))