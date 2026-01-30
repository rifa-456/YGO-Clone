from typing import List, TYPE_CHECKING
from engine.logger import Logger
from game.mechanics.enums import GameGroups
from game.scenes.duel.logic.commands.base_command import DuelCommand
from game.scenes.duel.logic.turn_handler import GamePhase

if TYPE_CHECKING:
    from game.entities.card.card import Card
    from game.entities.slot.slot import Slot


class SummonCommand(DuelCommand):
    def __init__(self, card: "Card", slot: "Slot", tributes: List["Slot"] = None):
        self.card = card
        self.slot = slot
        self.tributes = tributes if tributes is not None else []
        self._is_fulfillment = tributes is not None

    def execute(self, state, mediator):
        if not self._validate_phase(state):
            return

        if not self._is_fulfillment:
            if not self._validate_slot(self.slot):
                mediator.summon_failed.emit("Slot Occupied")
                return

            required_tributes = self._get_tribute_cost(self.card)
            if required_tributes > 0:
                self._handle_tribute_request(state, mediator, required_tributes)
                return

        self._process_tributes(mediator)
        self._finalize_summon(mediator)

    def _validate_phase(self, state) -> bool:
        if state.turn_handler.current_phase != GamePhase.MAIN:
            Logger.warn("Summon Failed: Not Main Phase", "SummonCommand")
            return False
        return True

    def _validate_slot(self, slot) -> bool:
        if slot.is_occupied():
            Logger.warn(
                f"Summon Failed: Slot {slot.row},{slot.col} occupied.", "SummonCommand"
            )
            return False
        return True

    def _get_tribute_cost(self, card) -> int:
        level = card.stats.data.level
        if level >= 7:
            return 2
        if level >= 5:
            return 1
        return 0

    def _handle_tribute_request(self, state, mediator, cost: int):
        available = sum(
            1 for c in range(5) if state.player_board.get_slot(1, c).is_occupied()
        )

        if available >= cost:
            Logger.info(
                f"Summon requires {cost} tributes. Requesting selection.",
                "SummonCommand",
            )
            mediator.summon_requires_tribute.emit(self.card, self.slot, cost)
        else:
            mediator.summon_failed.emit("Insufficient Tributes")

    def _process_tributes(self, mediator):
        for slot in self.tributes:
            sacrificed_card = slot.remove_card()
            if sacrificed_card:
                mediator.send_to_graveyard(sacrificed_card)

    def _finalize_summon(self, mediator):
        board_node = self.slot.get_parent()

        if not hasattr(board_node, "logic"):
            Logger.error("SummonCommand: Slot parent is not a Board!", "SummonCommand")
            return

        is_enemy_slot = board_node.logic.is_enemy
        target_group = (
            GameGroups.ENEMY_MONSTERS if is_enemy_slot else GameGroups.PLAYER_MONSTERS
        )

        self.card.add_to_group(target_group)
        Logger.info(
            f"Summon Finalized: {self.card.name} -> {target_group}", "SummonCommand"
        )
        mediator.summon_approved.emit(self.card, self.slot)
