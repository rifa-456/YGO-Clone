from typing import List, Optional, TYPE_CHECKING
from engine.ui.control import Control
from engine.ui.containers.margin_container import MarginContainer
from engine.ui.enums import SizeFlag, FocusMode, MouseFilter
from engine.scene.main.signal import Signal
from engine.scene.main.node import Node
from engine.math.datatypes.vector2 import Vector2
from game.entities.card.card import Card

if TYPE_CHECKING:
    from game.entities.board.board import Board


class Hand(Control):
    """
    Root Entity for the Player's Hand.
    Refactored: Uses custom layout logic (Control) to allow
    overlapping cards and precise Z-index control.
    """

    CARD_WIDTH: int = 128
    CARD_OVERLAP: int = 20

    SELECTED_Y_OFFSET: int = 40
    INACTIVE_Y_OFFSET: int = 100

    BASE_Z_INDEX: int = 50
    FOCUSED_CARD_Z_BONUS: int = 100

    OFFSET_ACTIVE_BOTTOM: int = 20
    OFFSET_INACTIVE_BOTTOM: int = -50

    def __init__(
        self,
        name: str = "PlayerHand",
        scale: float = 1.0,
        interaction_enabled: bool = True
    ):
        super().__init__(name=name)
        self.cards: List[Card] = []

        self.hand_scale = Vector2(scale, scale)
        self.interaction_enabled = interaction_enabled

        self.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self.size_flags_vertical = SizeFlag.SHRINK_END

        scaled_height = 200 * scale
        self.custom_minimum_size = Vector2(0, scaled_height)

        self.focus_mode = FocusMode.ALL if interaction_enabled else FocusMode.NONE
        self.mouse_filter = MouseFilter.IGNORE

        self.on_card_chosen = Signal("on_card_chosen")
        self.on_focus_lost = Signal("on_focus_lost")
        self.on_focus_state_changed = Signal("on_focus_state_changed")

        self.card_hovered = Signal("card_hovered")

        self._is_active_state = False
        self._connected_board: Optional["Board"] = None
        self._is_enemy_hand: bool = False

        self._hovered_card: Optional["Card"] = None

    def _ready(self):
        super()._ready()
        self.z_index = self.BASE_Z_INDEX
        self._enter_tree()

    def add_card(self, card: Card):
        """Adds a card to the hand and wires signals."""
        self.cards.append(card)
        card.name = f"Card_{len(self.cards)}"

        card.scale = self.hand_scale

        if not card.on_selected.is_connected(self._on_card_selected):
            card.on_selected.connect(self._on_card_selected)

        if not card.mouse_entered.is_connected(self._on_card_mouse_entered):
            card.mouse_entered.connect(lambda: self._on_card_mouse_entered(card))

        if not card.mouse_exited.is_connected(self._on_card_mouse_exited):
            card.mouse_exited.connect(lambda: self._on_card_mouse_exited(card))

        if not card.focus_entered.is_connected(self._on_card_focus_entered):
            card.focus_entered.connect(lambda: self._on_card_focus_entered(card))

        if not card.focus_exited.is_connected(self.queue_sort):
            card.focus_exited.connect(self.queue_sort)

        super().add_child(card)

        card.reset_visual_transform()

        self._refresh_board_connections()
        self.queue_sort()

    def remove_card(self, card: Card):
        """Removes a card from the hand and cleans up signals."""
        if card in self.cards:
            if card.on_selected.is_connected(self._on_card_selected):
                card.on_selected.disconnect(self._on_card_selected)

            if self._hovered_card == card:
                self._hovered_card = None

            self.cards.remove(card)
            super().remove_child(card)

            for i, c in enumerate(self.cards):
                c.name = f"Card_{i + 1}"

            self._refresh_board_connections()
            self.queue_sort()

    def queue_sort(self):
        """
        Triggers a layout update.
        """
        self._update_layout()

    def _on_card_mouse_entered(self, card: Card):
        """Tracks the currently hovered card and updates layout."""
        self._hovered_card = card
        self._emit_hover(card)
        self.queue_sort()

    def _on_card_mouse_exited(self, card: Card):
        """Clears hover state if the mouse left the current card."""
        if self._hovered_card == card:
            self._hovered_card = None
        self.queue_sort()

    def _on_card_focus_entered(self, card: Card):
        """Triggers hover signal on focus and updates layout."""
        self._emit_hover(card)
        self.queue_sort()

    def _update_layout(self):
        """
        Calculates position and Z-index for all cards.
        Implements: Overlap, Centering, and Focus Pop-up (if enabled).
        """
        count = len(self.cards)
        if count == 0:
            return

        self._update_card_neighbors()
        scaled_card_width = self.CARD_WIDTH * self.hand_scale.x
        scaled_overlap = self.CARD_OVERLAP * self.hand_scale.x
        step_x = scaled_card_width - scaled_overlap
        total_width = ((count - 1) * step_x) + scaled_card_width
        start_x = (self.size.x - total_width) / 2.0
        base_y = 0.0
        if self.interaction_enabled and not self._is_active_state:
            base_y += self.INACTIVE_Y_OFFSET

        for i, card in enumerate(self.cards):
            if card.scale != self.hand_scale:
                card.scale = self.hand_scale

            target_x = start_x + (i * step_x)
            target_y = base_y

            z_layer = i

            if self.interaction_enabled:
                is_highlighted = (card == self._hovered_card) or card.has_focus()
                if is_highlighted:
                    target_y -= self.SELECTED_Y_OFFSET
                    z_layer += self.FOCUSED_CARD_Z_BONUS

            card.position = Vector2(target_x, target_y)

            card.z_index = z_layer

    def _notification(self, what: int):
        """Handle engine notifications for resizing."""
        super()._notification(what)
        if what == self.NOTIFICATION_RESIZED:
            self.queue_sort()
        elif what == self.NOTIFICATION_SORT_CHILDREN:
            self.queue_sort()

    def _enter_tree(self):
        super()._enter_tree()
        viewport = self.get_viewport()
        if viewport and not viewport.gui_focus_changed.is_connected(
                self._on_viewport_focus_changed
        ):
            viewport.gui_focus_changed.connect(self._on_viewport_focus_changed)

    def _emit_hover(self, card: Card):
        """Relays the child event to the scene."""
        self.card_hovered.emit(card)
        self.queue_sort()

    def connect_to_board(self, board: "Board", is_enemy: bool = False):
        self._connected_board = board
        self._is_enemy_hand = is_enemy
        self._refresh_board_connections()

    def _refresh_board_connections(self):
        if not self._connected_board:
            return

        if self._is_enemy_hand:
            from_board_side = "top"
            to_board_side = "bottom"
        else:
            from_board_side = "bottom"
            to_board_side = "top"

        for c in range(5):
            back_slot = self._connected_board.logic.get_slot(1, c)
            if back_slot:
                setattr(back_slot, f"focus_neighbor_{from_board_side}", "")

        if self.cards:
            for c in range(min(5, len(self.cards))):
                back_slot = self._connected_board.logic.get_slot(1, c)
                if c < len(self.cards) and back_slot:
                    hand_card = self.cards[c]
                    path_to_card = back_slot.get_path_to(hand_card)
                    setattr(
                        back_slot, f"focus_neighbor_{from_board_side}", path_to_card
                    )
                    path_to_slot = hand_card.get_path_to(back_slot)
                    setattr(hand_card, f"focus_neighbor_{to_board_side}", path_to_slot)

            if len(self.cards) > 5:
                rightmost_back = self._connected_board.logic.get_slot(1, 4)
                if rightmost_back:
                    for i in range(5, len(self.cards)):
                        hand_card = self.cards[i]
                        path_to_slot = hand_card.get_path_to(rightmost_back)
                        setattr(
                            hand_card, f"focus_neighbor_{to_board_side}", path_to_slot
                        )

    def _on_viewport_focus_changed(self, control: Optional[Node]):
        is_child_focused = False
        if control:
            current = control
            while current:
                if current == self:
                    is_child_focused = True
                    break
                current = current.parent

        if control == self:
            is_child_focused = True

        state_changed = self._is_active_state != is_child_focused

        if state_changed:
            self._is_active_state = is_child_focused
            self.on_focus_state_changed.emit(is_child_focused)
            self._update_hand_position()
            self.queue_sort()

    def _update_hand_position(self):
        """
        Adjusts the parent MarginContainer boundaries.
        Skipped if interaction is disabled (hand remains static).
        """
        if not self.interaction_enabled:
            return

        parent = self.get_parent()
        if isinstance(parent, MarginContainer):
            target_margin = self.OFFSET_ACTIVE_BOTTOM if self._is_active_state else self.OFFSET_INACTIVE_BOTTOM
            parent.add_constant_override("margin_bottom", target_margin)

    def _on_card_selected(self, card: Card):
        self.on_card_chosen.emit(card)

    def _update_card_neighbors(self):
        """
        Links the cards together for UI navigation (Left/Right).
        """
        card_count = len(self.cards)
        for i, card in enumerate(self.cards):
            if not isinstance(card, Control):
                continue

            if i > 0:
                prev_card = self.cards[i - 1]
                card.focus_neighbor_left = card.get_path_to(prev_card)
            else:
                card.focus_neighbor_left = ""

            if i < card_count - 1:
                next_card = self.cards[i + 1]
                card.focus_neighbor_right = card.get_path_to(next_card)
            else:
                card.focus_neighbor_right = ""

    def grab_focus(self):
        """Pass focus to the first available card."""
        if self.cards:
            self.cards[0].grab_focus()
        else:
            super().grab_focus()