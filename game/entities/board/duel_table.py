from typing import List
import numpy as np

from engine.ui.control import Control, LayoutPreset, SizeFlag, MouseFilter
from engine.math.datatypes.vector2 import Vector2
from engine.math.algorithms.homography import compute_homography, apply_homography, apply_homography_batch
from game.entities.slot.slot import Slot


class DuelTable(Control):
    """
    The Single Source of Truth for the Duel Field Geometry.
    Provides High-Performance Batch Transformation APIs.
    """

    TABLE_TOP_WIDTH_PCT = 0.70
    TABLE_BOTTOM_WIDTH_PCT = 1.0
    TABLE_TOP_Y_PCT = 0.20
    TABLE_BOTTOM_Y_PCT = 0.85

    GRID_ROWS = 4
    GRID_COLS = 5
    GRID_GAP = 3.0

    PERIPHERAL_SCALE = 0.55
    PERIPHERAL_GAP = 20.0
    PERIPHERAL_VERTICAL_OFFSET = -160.0
    PERIPHERAL_STACK_GAP = 3.0

    BOARD_GAP = 50.0

    def __init__(self, name: str = "DuelTable"):
        super().__init__(name=name)
        self._homography_matrix: List[List[float]] = []
        self._homography_matrix_np: np.ndarray = np.zeros((3, 3), dtype=np.float64)
        self._logical_size = Vector2(0, 0)
        self.side_margin = 0.0
        self.grid_start_x = 0.0
        self._calculate_logical_size()
        self.set_anchors_preset(LayoutPreset.FULL_RECT)
        self.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self.size_flags_vertical = SizeFlag.EXPAND_FILL
        self.mouse_filter = MouseFilter.IGNORE

    @classmethod
    def get_peripheral_size(cls) -> Vector2:
        """Returns the scaled size for peripheral slots (Deck, Grave, Field, Extra)."""
        w = float(Slot.CARD_WIDTH) * cls.PERIPHERAL_SCALE
        h = float(Slot.CARD_HEIGHT) * cls.PERIPHERAL_SCALE
        return Vector2(w, h)

    def _calculate_logical_size(self):
        """
        Calculates the flat 2D size of the full Playmat.
        Layout: [Enemy Peripherals] -> [Enemy Grid] -> [GAP] -> [Player Grid] -> [Player Peripherals]
        """
        sq_w = float(Slot.SQUARE_WIDTH)
        sq_h = float(Slot.SQUARE_HEIGHT)

        peri_size = self.get_peripheral_size()
        card_h_scaled = peri_size.y
        card_w_scaled = peri_size.x

        grid_width = (sq_w * self.GRID_COLS) + (self.GRID_GAP * (self.GRID_COLS - 1))

        self.side_margin = card_w_scaled + self.PERIPHERAL_GAP
        total_w = grid_width + (self.side_margin * 2)

        single_grid_h = (sq_h * 2) + self.GRID_GAP

        peripheral_height = (card_h_scaled * 2) + self.PERIPHERAL_STACK_GAP

        single_board_total_h = single_grid_h + self.PERIPHERAL_VERTICAL_OFFSET + peripheral_height
        total_h = (single_board_total_h * 2) + self.BOARD_GAP
        self._logical_size = Vector2(total_w, total_h)

    def get_logical_size(self) -> Vector2:
        return self._logical_size

    def _notification(self, what: int):
        super()._notification(what)
        if what == self.NOTIFICATION_ENTER_TREE:
            parent = self.get_parent()
            if parent and isinstance(parent, Control):
                if not parent.resized.is_connected(self._on_parent_resized):
                    parent.resized.connect(self._on_parent_resized)
            self._update_homography()

        elif what == self.NOTIFICATION_RESIZED:
            self._update_homography()

        elif what == self.NOTIFICATION_TRANSFORM_CHANGED:
            self._update_homography()

    def _on_parent_resized(self):
        """Forces the DuelTable to snap to the parent's new size."""
        self._update_layout()
        self._update_homography()

    def _update_homography(self):
        """
        Recomputes the matrix mapping Logical Grid → DuelTable Local Space Trapezoid.
        """
        w, h = self.size.x, self.size.y

        cx = w / 2.0
        top_w_px = w * self.TABLE_TOP_WIDTH_PCT
        btm_w_px = w * self.TABLE_BOTTOM_WIDTH_PCT
        top_y_px = h * self.TABLE_TOP_Y_PCT
        btm_y_px = h * self.TABLE_BOTTOM_Y_PCT

        local_tl = Vector2(cx - (top_w_px / 2), top_y_px)
        local_tr = Vector2(cx + (top_w_px / 2), top_y_px)
        local_br = Vector2(cx + (btm_w_px / 2), btm_y_px)
        local_bl = Vector2(cx - (btm_w_px / 2), btm_y_px)

        gt = self.get_global_transform()
        src_rect = [
            Vector2(0, 0),
            Vector2(self._logical_size.x, 0),
            Vector2(self._logical_size.x, self._logical_size.y),
            Vector2(0, self._logical_size.y)
        ]

        dst_rect = [local_tl, local_tr, local_br, local_bl]

        self._homography_matrix = compute_homography(src_rect, dst_rect)

        for r in range(3):
            for c in range(3):
                self._homography_matrix_np[r, c] = self._homography_matrix[r][c]

        for child in self.children:
            if hasattr(child, "on_table_resized"):
                child.on_table_resized()

    def transform_point(self, logical_point: Vector2) -> Vector2:
        """
        Transforms a point from Logical Grid Space to DuelTable Local Space.
        CHANGED: Returns local coordinates, not global.
        """
        if not self._homography_matrix:
            return logical_point

        sx, sy = apply_homography(self._homography_matrix, logical_point.x, logical_point.y)
        return Vector2(sx, sy)

    def transform_geometry_batch(self, points: List[Vector2]) -> List[Vector2]:

        count = len(points)
        if count == 0:
            return []

        in_arr = np.zeros((count, 2), dtype=np.float64)
        for i in range(count):
            v = points[i]
            in_arr[i, 0] = v.x
            in_arr[i, 1] = v.y

        out_arr = np.zeros((count, 2), dtype=np.float64)
        apply_homography_batch(self._homography_matrix_np, in_arr, out_arr)

        result = []
        for i in range(count):
            result.append(Vector2(out_arr[i, 0], out_arr[i, 1]))

        return result