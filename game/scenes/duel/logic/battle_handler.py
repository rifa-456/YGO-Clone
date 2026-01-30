from dataclasses import dataclass, field
from typing import List, Optional
from engine.core.object import Object
from engine.logger import Logger
from game.entities.card.card import Card
from game.entities.card.card_state import CardState


@dataclass
class BattleResult:

    winner: Optional[Card] = None
    destroyed_cards: List[Card] = field(default_factory=list)
    damage_to_attacker: int = 0
    damage_to_defender: int = 0
    is_draw: bool = False


class BattleHandler(Object):

    @staticmethod
    def calculate_battle(attacker: Card, defender: Card) -> BattleResult:
        result = BattleResult()
        atk_val = attacker.stats.current_atk
        def_is_attack_pos = defender.logic.current_state == CardState.FIELD_ATTACK
        if def_is_attack_pos:
            target_val = defender.stats.current_atk
        else:
            target_val = defender.stats.current_def

        Logger.info(
            f"Battle Calc: {atk_val} (ATK) vs {target_val} ({'ATK' if def_is_attack_pos else 'DEF'})",
            "BattleHandler",
        )
        if def_is_attack_pos:
            if atk_val > target_val:
                result.winner = attacker
                result.destroyed_cards.append(defender)
                result.damage_to_defender = atk_val - target_val
            elif atk_val == target_val:
                result.is_draw = True
                result.destroyed_cards.append(attacker)
                result.destroyed_cards.append(defender)
            else:
                result.winner = defender
                result.destroyed_cards.append(attacker)
                result.damage_to_attacker = target_val - atk_val

        else:
            if atk_val > target_val:
                result.winner = attacker
                result.destroyed_cards.append(defender)
            elif atk_val == target_val:
                result.is_draw = True
            else:
                result.damage_to_attacker = target_val - atk_val

        return result
