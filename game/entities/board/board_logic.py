from typing import List, Optional, Tuple
from game.entities.slot.slot import Slot
from game.entities.slot.slot_enums import SlotType


class BoardLogic:
    def __init__(self, is_enemy: bool, rows: int = 2, cols: int = 5):
        self.is_enemy = is_enemy
        self.rows = rows
        self.cols = cols
        self._grid: List[List[Optional["Slot"]]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]
        self._field_slot: Optional["Slot"] = None
        self._graveyard_slot: Optional["Slot"] = None
        self._deck_slot: Optional["Slot"] = None
        self._extra_deck_slot: Optional["Slot"] = None

    def get_logical_coords(self, visual_index: int) -> Tuple[int, int]:
        visual_row = visual_index // self.cols
        visual_col = visual_index % self.cols
        if self.is_enemy:
            logical_row = 1 - visual_row
            logical_col = (self.cols - 1) - visual_col
        else:
            logical_row = visual_row
            logical_col = visual_col

        return logical_row, logical_col

    def register_slot(self, slot: "Slot", row: int, col: int):
        """Registers a slot into the grid or as a special zone based on type."""
        if slot.slot_type in (SlotType.MONSTER, SlotType.SPELL_TRAP):
            if self._is_valid(row, col):
                self._grid[row][col] = slot
        elif slot.slot_type == SlotType.FIELD:
            self._field_slot = slot
        elif slot.slot_type == SlotType.GRAVEYARD:
            self._graveyard_slot = slot
        elif slot.slot_type == SlotType.DECK:
            self._deck_slot = slot
        elif slot.slot_type == SlotType.EXTRA_DECK:
            self._extra_deck_slot = slot

    def get_slot(self, row: int, col: int) -> Optional["Slot"]:
        if self._is_valid(row, col):
            return self._grid[row][col]
        return None

    def get_deck_slot(self) -> Optional["Slot"]:
        return self._deck_slot

    def get_graveyard_slot(self) -> Optional["Slot"]:
        return self._graveyard_slot

    def get_field_slot(self) -> Optional["Slot"]:
        return self._field_slot

    def get_extra_deck_slot(self) -> Optional["Slot"]:
        return self._extra_deck_slot

    def _is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def _get_first_empty_slot(self, row: int) -> Optional["Slot"]:
        """
        Scans a specific row for the first available slot.
        Used by InputController for auto-focusing during summon sequences.
        """
        if row < 0 or row >= self.rows:
            return None

        for col in range(self.cols):
            slot = self._grid[row][col]
            if slot and not slot.is_occupied():
                return slot
        return None
