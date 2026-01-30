from typing import Optional, List, Tuple
from engine.math.datatypes.vector2 import Vector2
from engine.ui import Control, SizeFlag, LayoutPreset
from engine.ui.enums import MouseFilter
from game.entities.slot.slot import Slot
from engine.scene.main.signal import Signal
from .board_logic import BoardLogic
from ..slot.slot_enums import SlotType
from .duel_table import DuelTable


class Board(Control):
    """
    Logical container for one player's side (2 rows).
    Now completely reliant on DuelTable for geometry configuration.
    """

    def __init__(self, is_enemy: bool = False, name: str = "Board"):
        super().__init__(name=name)
        self.logic = BoardLogic(is_enemy=is_enemy)
        self._visual_slots: List[Slot] = []
        self._visual_grid: List[List[Optional[Slot]]] = []
        self.row_offset = 0 if is_enemy else 2

        self.slot_hovered = Signal("slot_hovered")

        self._setup_grid()
        self._setup_focus_neighbors()

        self.set_anchors_preset(LayoutPreset.FULL_RECT)
        self.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self.size_flags_vertical = SizeFlag.EXPAND_FILL
        self.mouse_filter = MouseFilter.IGNORE

    def _setup_grid(self):
        """
        Instantiates Slots and wires their internal signals to the Board aggregator.
        Explicitly names peripheral slots to prevent ID collisions.
        """
        self._visual_grid = []
        grid_size = Vector2(Slot.SQUARE_WIDTH, Slot.SQUARE_HEIGHT)
        peri_size = DuelTable.get_peripheral_size()

        def _wire_slot(s: Slot):
            s.focus_entered.connect(lambda: self.slot_hovered.emit(s))
            s.mouse_entered.connect(lambda: self.slot_hovered.emit(s))

        for r in range(self.logic.rows):
            visual_row_list = []
            for c in range(self.logic.cols):
                logical_row, logical_col = self.logic.get_logical_coords(r * self.logic.cols + c)
                s_type = SlotType.MONSTER if logical_row == 0 else SlotType.SPELL_TRAP
                slot = Slot(logical_row, logical_col, s_type, self._get_slot_texture(s_type), custom_size=grid_size)
                self.logic.register_slot(slot, logical_row, logical_col)
                self.add_child(slot)
                _wire_slot(slot)
                self._visual_slots.append(slot)
                visual_row_list.append(slot)
            self._visual_grid.append(visual_row_list)

        self.field_slot = Slot(-1, -1, SlotType.FIELD, Slot.KEY_SLOT_FIELD, custom_size=peri_size, name="Slot_Field")
        self.logic.register_slot(self.field_slot, -1, -1)
        self.add_child(self.field_slot)
        _wire_slot(self.field_slot)
        self._visual_slots.append(self.field_slot)

        self.grave_slot = Slot(-1, -1, SlotType.GRAVEYARD, Slot.KEY_SLOT_GRAVE, custom_size=peri_size,
                               name="Slot_Graveyard")
        self.logic.register_slot(self.grave_slot, -1, -1)
        self.add_child(self.grave_slot)
        _wire_slot(self.grave_slot)
        self._visual_slots.append(self.grave_slot)

        self.deck_slot = Slot(-1, -1, SlotType.DECK, Slot.KEY_SLOT_NORMAL, custom_size=peri_size, name="Slot_Deck")
        self.logic.register_slot(self.deck_slot, -1, -1)
        self.add_child(self.deck_slot)
        _wire_slot(self.deck_slot)
        self._visual_slots.append(self.deck_slot)

        self.extra_deck_slot = Slot(-1, -1, SlotType.EXTRA_DECK, Slot.KEY_SLOT_EXTRA, custom_size=peri_size,
                                    name="Slot_ExtraDeck")
        self.logic.register_slot(self.extra_deck_slot, -1, -1)
        self.add_child(self.extra_deck_slot)
        _wire_slot(self.extra_deck_slot)
        self._visual_slots.append(self.extra_deck_slot)

    def on_table_resized(self):
        """Called by DuelTable when geometry changes."""
        self._update_visual_geometry()

    def _update_visual_geometry(self):
        """
        Computes slot positions in DuelTable's logical coordinate space,
        transforms them via DuelTable's homography to DuelTable's local space,
        then converts to Board's local space for children.
        """

        parent = self.get_parent()
        grid_gap = parent.GRID_GAP
        board_gap = parent.BOARD_GAP
        peri_gap_y = parent.PERIPHERAL_VERTICAL_OFFSET
        peri_stack_gap = getattr(parent, "PERIPHERAL_STACK_GAP", 10.0)
        side_offset = parent.side_margin

        sq_w = float(Slot.SQUARE_WIDTH)
        sq_h = float(Slot.SQUARE_HEIGHT)

        peri_size = DuelTable.get_peripheral_size()
        peri_w = peri_size.x
        peri_h = peri_size.y

        grid_block_h = (sq_h * 2) + grid_gap
        peripheral_zone_h = (peri_h * 2) + peri_stack_gap
        single_board_h = grid_block_h + peri_gap_y + peripheral_zone_h

        if self.logic.is_enemy:
            grid_start_y = peripheral_zone_h + peri_gap_y
        else:
            base_y = single_board_h + board_gap
            grid_start_y = base_y

        batch_requests: List[Tuple[Slot, List[Vector2]]] = []
        all_points_flat: List[Vector2] = []

        for r in range(self.logic.rows):
            for c in range(self.logic.cols):
                slot = self._visual_grid[r][c]
                if not slot:
                    continue
                lx = side_offset + (c * (sq_w + grid_gap))
                ly = grid_start_y + (r * (sq_h + grid_gap))
                rx = lx + sq_w
                uy = ly + sq_h
                quad = [Vector2(lx, ly), Vector2(rx, ly), Vector2(rx, uy), Vector2(lx, uy)]
                batch_requests.append((slot, quad))
                all_points_flat.extend(quad)

        self._gather_peripheral_slots(
            batch_requests,
            all_points_flat,
            grid_start_y,
            sq_h,
            peri_w,
            peri_h,
            peri_gap_y,
            side_offset,
            peri_stack_gap,
            parent.get_logical_size().x,
            grid_gap
        )

        transformed_flat = parent.transform_geometry_batch(all_points_flat)
        current_idx = 0
        for slot, _ in batch_requests:
            duel_table_local_quad = transformed_flat[current_idx: current_idx + 4]
            board_local_quad = duel_table_local_quad
            slot.set_quad_geometry(board_local_quad)
            current_idx += 4

    def _gather_peripheral_slots(self, requests: list, flat_list: list, grid_start_y: float, sq_h: float,
                                 peri_w: float, peri_h: float,
                                 peri_gap_y: float,
                                 side_offset: float, stack_gap: float, logical_width: float, grid_gap: float):
        """
        Gathers peripheral slot positions in DuelTable's LOGICAL coordinate space.
        """
        is_enemy = self.logic.is_enemy
        left_wing_x = 0.0
        right_wing_x = logical_width - peri_w

        def add_req(slot, x, y):
            quad = [
                Vector2(x, y),
                Vector2(x + peri_w, y),
                Vector2(x + peri_w, y + peri_h),
                Vector2(x, y + peri_h)
            ]
            requests.append((slot, quad))
            flat_list.extend(quad)

        field_slot = self.logic.get_field_slot()
        extra_slot = self.logic.get_extra_deck_slot()
        deck_slot = self.logic.get_deck_slot()
        grave_slot = self.logic.get_graveyard_slot()

        if is_enemy:
            base_y = 0.0
            deck_y = base_y
            grave_y = base_y + peri_h + stack_gap
            extra_y = base_y
            field_y = base_y + peri_h + stack_gap

            if deck_slot: add_req(deck_slot, left_wing_x, deck_y)
            if grave_slot: add_req(grave_slot, left_wing_x, grave_y)
            if extra_slot: add_req(extra_slot, right_wing_x, extra_y)
            if field_slot: add_req(field_slot, right_wing_x, field_y)

        else:
            grid_bottom = grid_start_y + (sq_h * 2) + grid_gap
            peripheral_start_y = grid_bottom + peri_gap_y
            grave_y = peripheral_start_y
            deck_y = grave_y + peri_h + stack_gap
            field_y = peripheral_start_y
            extra_y = field_y + peri_h + stack_gap

            if deck_slot: add_req(deck_slot, right_wing_x, deck_y)
            if grave_slot: add_req(grave_slot, right_wing_x, grave_y)
            if field_slot: add_req(field_slot, left_wing_x, field_y)
            if extra_slot: add_req(extra_slot, left_wing_x, extra_y)

    @staticmethod
    def _get_slot_texture(slot_type: SlotType) -> str:
        if slot_type == SlotType.FIELD:
            return Slot.KEY_SLOT_FIELD
        elif slot_type == SlotType.GRAVEYARD:
            return Slot.KEY_SLOT_GRAVE
        elif slot_type == SlotType.EXTRA_DECK:
            return Slot.KEY_SLOT_EXTRA
        return Slot.KEY_SLOT_NORMAL

    def _setup_focus_neighbors(self):
        """
        Sets navigation based on Visual Grid position.
        Explicitly handles Field/Grave/Deck/Extra wiring to Grid Rows.
        """
        from engine.logger import Logger

        rows = len(self._visual_grid)
        cols = len(self._visual_grid[0]) if rows > 0 else 0

        def _link(node_a: Control, side_a: str, node_b: Control, side_b: str):
            if not node_a or not node_b:
                return

            setattr(node_a, f"focus_neighbor_{side_a}", node_a.get_path_to(node_b))
            setattr(node_b, f"focus_neighbor_{side_b}", node_b.get_path_to(node_a))
            Logger.debug(f"Linked {node_a.name} ({side_a}) <-> {node_b.name} ({side_b})", "Board")

        for r in range(rows):
            for c in range(cols):
                slot = self._visual_grid[r][c]
                if not slot: continue

                if c < cols - 1:
                    right = self._visual_grid[r][c + 1]
                    _link(slot, "right", right, "left")

                if r < rows - 1:
                    bottom = self._visual_grid[r + 1][c]
                    _link(slot, "bottom", bottom, "top")

        if cols == 0:
            return
        is_enemy = self.logic.is_enemy

        v_row_top = 0
        v_row_btm = 1

        slot_top_left = self._visual_grid[v_row_top][0]
        slot_top_right = self._visual_grid[v_row_top][cols - 1]
        slot_btm_left = self._visual_grid[v_row_btm][0]
        slot_btm_right = self._visual_grid[v_row_btm][cols - 1]

        if not is_enemy:
            if self.field_slot:
                _link(self.field_slot, "right", slot_top_left, "left")
            if self.extra_deck_slot:
                _link(self.extra_deck_slot, "right", slot_btm_left, "left")

            if self.grave_slot:
                _link(self.grave_slot, "left", slot_top_right, "right")
            if self.deck_slot:
                _link(self.deck_slot, "left", slot_btm_right, "right")

            _link(self.field_slot, "bottom", self.extra_deck_slot, "top")
            _link(self.grave_slot, "bottom", self.deck_slot, "top")

        else:
            if self.deck_slot:
                _link(self.deck_slot, "right", slot_top_left, "left")
            if self.grave_slot:
                _link(self.grave_slot, "right", slot_btm_left, "left")

            if self.extra_deck_slot:
                _link(self.extra_deck_slot, "left", slot_top_right, "right")
            if self.field_slot:
                _link(self.field_slot, "left", slot_btm_right, "right")

            _link(self.deck_slot, "bottom", self.grave_slot, "top")
            _link(self.extra_deck_slot, "bottom", self.field_slot, "top")

        Logger.info(f"Focus Neighbors Setup Complete for {self.name}", "Board")

    def get_slot(self, row: int, col: int) -> Slot:
        slot = self.logic.get_slot(row, col)
        if slot: return slot
        raise ValueError(f"Slot not found at {row}, {col}")

    def get_first_empty_slot(self, row: int) -> Optional[Slot]:
        return self.logic._get_first_empty_slot(row)

    def clear_highlights(self):
        for r in range(self.logic.rows):
            for c in range(self.logic.cols):
                slot = self.logic.get_slot(r, c)
                if slot: slot.visuals.set_highlight(False)

    def highlight_slot(self, row: int, col: int):
        self.clear_highlights()
        slot = self.logic.get_slot(row, col)
        if slot: slot.visuals.set_highlight(True)

    def _notification(self, what: int):
        super()._notification(what)
        if what == self.NOTIFICATION_ENTER_TREE:
            self._update_visual_geometry()

    def set_row_isolation(self, row_index: int, isolated: bool):
        from engine.logger import Logger

        if not isolated:
            self._setup_focus_neighbors()
            Logger.info(f"Row {row_index} isolation lifted. Navigation reset.", "Board")
            return

        if 0 <= row_index < len(self._visual_grid):
            row_slots = self._visual_grid[row_index]
            row_len = len(row_slots)

            for i, slot in enumerate(row_slots):
                if not slot:
                    continue

                slot.focus_neighbor_top = slot.get_path()
                slot.focus_neighbor_bottom = slot.get_path()

                if i == 0:
                    slot.focus_neighbor_left = slot.get_path()

                if i == row_len - 1:
                    slot.focus_neighbor_right = slot.get_path()

            Logger.info(f"Row {row_index} isolated. Navigation clamped to grid.", "Board")