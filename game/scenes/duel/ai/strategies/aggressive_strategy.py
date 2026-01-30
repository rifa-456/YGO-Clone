from typing import Optional, List, Tuple, TYPE_CHECKING
from game.scenes.duel.ai.strategies.base_strategy import AIStrategy
from game.entities.card.card_state import CardState

if TYPE_CHECKING:
    from game.entities.card.card import Card
    from game.entities.slot.slot import Slot
    from game.entities.board.board import Board
    from game.entities.hand.hand import Hand


class AggressiveStrategy(AIStrategy):
    """
    Standard 'Beatdown' AI.
    - Summons highest ATK monster possible.
    - Attacks lowest DEF/ATK targets.
    - Sets monsters only if they can't survive in Attack position.
    """

    def decide_summon(
        self, hand: "Hand", my_board: "Board", opp_board: "Board"
    ) -> Optional[Tuple["Card", List["Slot"]]]:
        monsters = [c for c in hand.cards if "MONSTER" in c.stats.data.card_type.name]

        monsters.sort(key=lambda c: c.stats.data.atk, reverse=True)

        my_tributes = []
        for c in range(5):
            s = my_board.get_slot(1, c)
            if s.is_occupied():
                my_tributes.append(s)

        my_tributes.sort(key=lambda s: s.card_node.stats.current_atk)

        for m in monsters:
            req_tributes = self._get_tribute_cost(m)

            if len(my_tributes) >= req_tributes:
                tribute_slots = my_tributes[:req_tributes]
                return (m, tribute_slots)

        return None

    def decide_attack_target(
        self, attacker: "Card", opp_board: "Board"
    ) -> Optional["Slot"]:
        my_atk = attacker.stats.current_atk
        potential_targets = []

        for c in range(5):
            slot = opp_board.get_slot(1, c)
            if slot.is_occupied():
                potential_targets.append(slot)

        if not potential_targets:
            return None

        killable_atk = [
            s
            for s in potential_targets
            if s.card_node.logic.current_state == CardState.FIELD_ATTACK
            and s.card_node.stats.current_atk < my_atk
        ]
        if killable_atk:
            killable_atk.sort(key=lambda s: s.card_node.stats.current_atk, reverse=True)
            return killable_atk[0]

        killable_def = [
            s
            for s in potential_targets
            if s.card_node.logic.current_state == CardState.FIELD_DEFENSE
            and s.card_node.logic.face_up
            and s.card_node.stats.current_def < my_atk
        ]
        if killable_def:
            killable_def.sort(key=lambda s: s.card_node.stats.current_def, reverse=True)
            return killable_def[0]

        face_downs = [s for s in potential_targets if not s.card_node.logic.face_up]
        if face_downs:
            if my_atk > 1500 or len(potential_targets) == 1:
                return face_downs[0]

        return None

    def should_set_in_defense(self, card: "Card", opp_board: "Board") -> bool:
        enemy_max_atk = self._get_max_stat(opp_board, "atk")
        my_atk = card.stats.data.atk
        my_def = card.stats.data.def_

        if my_atk > enemy_max_atk:
            return False

        if my_def > enemy_max_atk:
            return True

        return True

    @staticmethod
    def _get_tribute_cost(card: "Card") -> int:
        """Determine tribute cost based on Level."""
        level = card.stats.data.level
        if level >= 7:
            return 2
        if level >= 5:
            return 1
        return 0

    @staticmethod
    def _get_max_stat(board: "Board", stat: str) -> int:
        """Helper to scan enemy board for highest threat."""
        max_val = 0
        for c in range(5):
            slot = board.get_slot(1, c)
            if slot.is_occupied() and slot.card_node.logic.face_up:
                val = (
                    slot.card_node.stats.current_atk
                    if stat == "atk"
                    else slot.card_node.stats.current_def
                )
                if val > max_val:
                    max_val = val
        return max_val
