from typing import TYPE_CHECKING
from engine.logger import Logger
from game.entities.card import Card
from game.entities.slot.slot import Slot

if TYPE_CHECKING:
    from ..duel_scene import DuelScene


class UISignals:
    def __init__(self, scene: "DuelScene"):
        self.scene = scene

    def wire(self) -> None:
        Logger.info("Wiring UI Signals...", "UISignals")
        self._wire_hud_interactions()
        self._wire_board_slots(self.scene.player_board)
        self._wire_status_panel()

    def _wire_status_panel(self):
        """
        Injects GameState into the StatusPanel and connects the turn signal.
        """
        if self.scene.status_panel and self.scene.mediator.game_state:
            self.scene.status_panel.assign_game_state(self.scene.mediator.game_state)

        if self.scene.turn_handler:
            self.scene.turn_handler.on_turn_start.connect(
                self.scene.status_panel.on_turn_started
            )

    def _wire_click_signals(self, board):
        for r in range(board.logic.rows):
            for c in range(board.logic.cols):
                try:
                    slot = board.get_slot(r, c)
                    if not slot.on_selected.is_connected(self._on_slot_clicked):
                        slot.on_selected.connect(self._on_slot_clicked)
                except ValueError:
                    continue

    def _wire_hud_interactions(self):
        """
        Connects Board and Hand aggregate signals to the HUD.
        """
        self.scene.hand.card_hovered.connect(self.on_hand_card_hover)
        self.scene.player_board.slot_hovered.connect(self._on_board_hover)
        self.scene.enemy_board.slot_hovered.connect(self._on_board_hover)
        self._wire_click_signals(self.scene.player_board)
        self._wire_click_signals(self.scene.enemy_board)

    def _wire_board_slots(self, board):
        """
        Connects input signals for all slots in the board.
        """
        for r in range(board.logic.rows):
            for c in range(board.logic.cols):
                try:
                    slot = board.get_slot(r, c)
                    slot.on_selected.connect(self._on_slot_clicked)
                    slot.mouse_entered.connect(lambda s=slot: self._on_board_hover(s))
                    slot.mouse_exited.connect(self._on_slot_exit)
                except ValueError:
                    continue

    def highlight_valid_slots(self):
        for c in range(5):
            slot = self.scene.player_board.get_slot(1, c)
            if slot and not slot.is_occupied():
                slot.visuals.set_highlight(True)

    def _on_slot_clicked(self, slot: Slot):
        self.scene.input_controller.handle_slot_clicked(slot)

    def on_position_confirmed(self, is_defense: bool):
        self.scene.input_controller.handle_position_confirmed(is_defense)

    def on_hand_card_hover(self, card: Card):
        if card:
            self._update_hud_with_card(card)

    def _on_board_hover(self, slot: Slot):
        """
        Unified handler for any slot hover (Player or Enemy).
        """
        card_node = slot.get_card()
        if card_node and isinstance(card_node, Card):
            if card_node.stats and card_node.stats.data:
                self.scene.card_panel.set_card(card_node.stats.data)
        else:
            self.scene.card_panel.reset_state()

    def _on_slot_exit(self):
        """
        Clears the HUD when the mouse leaves a slot.
        """
        self.scene.card_panel.reset_state()

    def _update_hud_with_card(self, card: Card):
        if isinstance(card, Card):
            self.scene.card_panel.set_card(card.stats.data)