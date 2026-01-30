from typing import Optional
from engine.core.object import Object
from engine.logger import Logger
from game.entities.card.card_state import CardState
from game.scenes.duel.ai.strategies.aggressive_strategy import AggressiveStrategy
from game.scenes.duel.ai.strategies.base_strategy import AIStrategy
from game.scenes.duel.logic.turn_handler import GamePhase, TurnOwner
from game.scenes.duel.logic.duel_mediator import DuelMediator
from game.scenes.duel.logic.turn_handler import TurnHandler


class AIAgent(Object):
    def __init__(
        self,
        mediator: DuelMediator,
        turn_system: TurnHandler,
        strategy: Optional[AIStrategy] = None,
    ):
        super().__init__()
        self.mediator = mediator
        self.turn_system = turn_system
        self.strategy = strategy if strategy else AggressiveStrategy()
        self._my_hand = None
        self._my_board = None
        self._opp_board = None
        self.turn_system.on_turn_owner_changed.connect(self._on_turn_change)
        self.turn_system.on_phase_change.connect(self._on_phase_change)

    def _update_context(self):
        """Syncs local references with the Mediator's state."""
        state = self.mediator.game_state
        if self.turn_system.current_turn_owner == TurnOwner.ENEMY:
            self._my_hand = state.enemy_hand
            self._my_board = state.enemy_board
            self._opp_board = state.player_board
        else:
            self._my_hand = state.player_hand
            self._my_board = state.player_board
            self._opp_board = state.enemy_board

    def _on_turn_change(self, owner: TurnOwner):
        if owner == TurnOwner.ENEMY:
            Logger.info("AI Turn Started. Initializing Context.", "AIAgent")
            self._update_context()

    def _on_phase_change(self, phase: GamePhase):
        if self.turn_system.current_turn_owner != TurnOwner.ENEMY:
            return

        if phase == GamePhase.MAIN:
            self._execute_main_phase()
        elif phase == GamePhase.BATTLE:
            self._execute_battle_phase()
        elif phase == GamePhase.END:
            Logger.info("AI Ending Turn.", "AIAgent")
            self.turn_system.next_phase()

    def _execute_main_phase(self):
        Logger.info("Enemy: Main Phase Execution", "AIAgent")
        self._try_activate_spells()
        summon_decision = self.strategy.decide_summon(
            self._my_hand, self._my_board, self._opp_board
        )
        if summon_decision:
            card, tributes = summon_decision
            self._perform_summon(card, tributes)

        self._set_remaining_backrow()
        self.turn_system.next_phase()

    def _execute_battle_phase(self):
        Logger.info("Enemy: Battle Phase Execution", "AIAgent")
        attackers = []
        for c in range(5):
            slot = self._my_board.get_slot(1, c)
            if slot.is_occupied():
                card = slot.card_node
                if card.logic.current_state == CardState.FIELD_ATTACK:
                    attackers.append(slot)

        attackers.sort(key=lambda s: s.card_node.stats.current_atk, reverse=True)
        for attacker_slot in attackers:
            target_slot = self.strategy.decide_attack_target(
                attacker_slot.card_node, self._opp_board
            )

            if target_slot:
                self.mediator.request_attack(attacker_slot, target_slot)
            elif self._is_enemy_field_empty():
                pass

        self.turn_system.next_phase()

    def _perform_summon(self, card, tributes):
        slot = self._my_board.get_first_empty_slot(1)
        if not slot:
            return

        should_set = self.strategy.should_set_in_defense(card, self._opp_board)
        target_state = CardState.FIELD_DEFENSE if should_set else CardState.FIELD_ATTACK
        card.set_state(target_state)
        if should_set:
            card.flip(False)
        Logger.info(
            f"AI Action: Summon {card.name} (Set={should_set}, Tributes={len(tributes)})",
            "AIAgent",
        )
        self.mediator.request_summon(card, slot)
        if tributes:
            self.mediator.fulfill_summon(card, slot, tributes)

    def _try_activate_spells(self):
        """Simple heuristic: Activate all Spells immediately."""
        hand_cards = list(self._my_hand.cards)
        for card in hand_cards:
            if card.stats.data.card_type.name == "SPELL":
                Logger.info(f"AI Action: Activating Spell {card.name}", "AIAgent")
                self.mediator.activate_spell(card)

    def _set_remaining_backrow(self):
        """Dump remaining non-monster cards face-down."""
        hand_cards = list(self._my_hand.cards)
        for card in hand_cards:
            if "MONSTER" not in card.stats.data.card_type.name:
                slot = self._my_board.get_first_empty_slot(0)
                if slot:
                    self.mediator.request_set_card(card, slot)

    def _is_enemy_field_empty(self) -> bool:
        for c in range(5):
            if self._opp_board.get_slot(1, c).is_occupied():
                return False
        return True
