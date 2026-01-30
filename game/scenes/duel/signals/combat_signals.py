from typing import TYPE_CHECKING
from engine.logger import Logger
from game.entities.card.card import Card
from game.entities.card.card_visual_mode import CardVisualMode

if TYPE_CHECKING:
    from ..duel_scene import DuelScene
    from game.entities.slot.slot import Slot
    from game.autoload.card_database import CardData


class CombatSignals:
    def __init__(self, scene: "DuelScene"):
        self.scene = scene

    def wire(self) -> None:
        Logger.info("Wiring Combat Signals...", "CombatSignals")
        self.scene.mediator.summon_approved.connect(self._execute_summon)

        self.scene.mediator.draw_approved.connect(self._execute_draw)

        self.scene.mediator.summon_requires_tribute.connect(
            self._on_summon_requires_tribute
        )
        self.scene.mediator.on_stats_changed.connect(
            self.scene.status_panel.on_stats_changed
        )
        self.scene.mediator.on_game_over.connect(self._on_game_over)

    def _execute_summon(self, card: Card, slot: "Slot"):
        card.set_visual_mode(CardVisualMode.FULL)

        target_state = getattr(self.scene, "target_summon_state", None)
        if target_state:
            card.set_state(target_state)

        self.scene.hand.remove_card(card)
        slot.assign_card(card)

    def _execute_draw(self, card_data: "CardData", is_player: bool):
        """
        Handles the visual instantiation of a drawn card.
        """
        target_hand = self.scene.hand if is_player else self.scene.enemy_hand
        card_node = Card(card_data)
        target_hand.add_card(card_node)
        if is_player:
            card_node.mouse_entered.connect(
                lambda: self.scene.signals.ui.on_hand_card_hover(card_node)
            )
            card_node.focus_entered.connect(
                lambda: self.scene.signals.ui.on_hand_card_hover(card_node)
            )
        else:
            card_node.set_visual_mode(CardVisualMode.BACK)

    def _on_summon_requires_tribute(self, card: Card, slot: "Slot", cost: int):
        self.scene.input_controller.handle_tribute_request(card, slot, cost)

    @staticmethod
    def _on_game_over(winner: str):
        Logger.info(f"!!! WINNER IS {winner} !!!", "DuelScene")