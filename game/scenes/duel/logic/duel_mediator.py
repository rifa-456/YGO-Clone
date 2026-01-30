import random
from typing import List, TYPE_CHECKING
from engine.core.object import Object
from engine.logger import Logger
from engine.scene.main.signal import Signal
from game.scenes.duel.logic.game_state import GameState
from game.scenes.duel.logic.commands.draw_command import DrawCommand
from game.scenes.duel.logic.commands.summon_command import SummonCommand
from game.scenes.duel.logic.commands.attack_command import AttackCommand
from game.scenes.duel.logic.turn_handler import GamePhase, TurnOwner
from game.mechanics.enums import GameGroups, EffectTrigger

if TYPE_CHECKING:
    from game.entities.card.card import Card
    from game.entities.slot.slot import Slot


class DuelMediator(Object):

    MAX_HAND_SIZE = 6

    def __init__(self):
        super().__init__()
        self.game_state = GameState()

        self.summon_approved = Signal("summon_approved")
        self.summon_failed = Signal("summon_failed")
        self.draw_approved = Signal("draw_approved")
        self.draw_failed = Signal("draw_failed")
        self.summon_requires_tribute = Signal("summon_requires_tribute")
        self.on_stats_changed = Signal("on_stats_changed")
        self.on_game_over = Signal("on_game_over")
        self.on_attack_declared = Signal("on_attack_declared")

    def setup(self, turn_system, p_board, e_board, p_hand, e_hand, p_deck, e_deck):
        self.game_state.configure(
            turn_system, p_board, e_board, p_hand, e_hand, p_deck, e_deck
        )
        self.game_state.turn_handler.bind_game_state(self.game_state)
        if not self.game_state.turn_handler.on_phase_change.is_connected(self._on_phase_changed):
            self.game_state.turn_handler.on_phase_change.connect(self._on_phase_changed)

        self.on_stats_changed.emit()
        Logger.info("DuelMediator Configured.", "DuelMediator")

    def _on_phase_changed(self, new_phase: GamePhase):
        if new_phase == GamePhase.END:
            self._enforce_hand_limit()

    def _enforce_hand_limit(self):
        current_owner = self.game_state.turn_handler.current_turn_owner

        hand = (
            self.game_state.player_hand
            if current_owner == TurnOwner.PLAYER
            else self.game_state.enemy_hand
        )

        excess = len(hand.cards) - self.MAX_HAND_SIZE
        if excess <= 0:
            return

        Logger.info(
            f"End Phase Rule: Discarding {excess} card(s) from {current_owner.name} Hand.",
            "DuelMediator",
        )

        for _ in range(excess):
            if not hand.cards:
                break
            card = hand.cards[random.randint(0, len(hand.cards) - 1)]

            hand.remove_card(card)

            self.send_to_graveyard(card)

    def request_draw(self, deck_logic=None, amount=1):
        cmd = DrawCommand(deck_logic, amount)
        cmd.execute(self.game_state, self)

    def request_summon(self, card: "Card", slot: "Slot"):
        cmd = SummonCommand(card, slot)
        cmd.execute(self.game_state, self)

    def fulfill_summon(self, card: "Card", slot: "Slot", tributes: List["Slot"]):
        cmd = SummonCommand(card, slot, tributes)
        cmd.execute(self.game_state, self)

    def request_attack(self, attacker: "Slot", target: "Slot"):
        cmd = AttackCommand(attacker.logic.card_node, target.logic.card_node)
        cmd.execute(self.game_state, self)

    def request_set_card(self, card: "Card", slot: "Slot"):
        if slot.is_occupied():
            return
        card.get_parent().remove_card(card)
        slot.assign_card(card)
        card.flip(False)
        Logger.info(f"Set Card {card.name}", "DuelMediator")

    def activate_spell(self, card: "Card"):
        if card.stats.data.card_type.name != "SPELL":
            return
        Logger.info(f"Activating Spell: {card.name}", "DuelMediator")
        self._resolve_effect_tree(card, None)
        self.send_to_graveyard(card)

    def send_to_graveyard(self, card: "Card"):
        if card.is_in_group(GameGroups.PLAYER_MONSTERS):
            card.remove_from_group(GameGroups.PLAYER_MONSTERS)
        if card.is_in_group(GameGroups.ENEMY_MONSTERS):
            card.remove_from_group(GameGroups.ENEMY_MONSTERS)

        if card.get_parent() and hasattr(card.get_parent(), "remove_card"):
            pass

        if card.get_parent():
            card.get_parent().remove_child(card)

        is_enemy = "Enemy" in card.get_path() if card.is_inside_tree() else False

        if not card.is_inside_tree():
            pass

        target_board = (
            self.game_state.enemy_board if is_enemy else self.game_state.player_board
        )

        if target_board:
            grave_slot = target_board.get_slot(1, 6)
            if grave_slot:
                grave_slot.assign_card(card)

        from game.entities.card.card_visual_mode import CardVisualMode
        card.set_visual_mode(CardVisualMode.FULL)
        Logger.info(f"Sent {card.name} to GY.", "DuelMediator")

    def check_reactive_traps(self, trigger: EffectTrigger, source_card: "Card") -> bool:
        """Legacy trap checking logic."""
        did_activate = False
        if not self.game_state.enemy_board:
            return False

        for col in range(5):
            slot = self.game_state.enemy_board.logic.get_slot(0, col)
            if slot and slot.is_occupied() and slot.card_node:
                trap = slot.card_node
                if trap.stats.data.card_type.name == "TRAP" and not trap.logic.face_up:
                    if trap.stats.data.effect_trigger == trigger:
                        Logger.info(f"Trap Triggered: {trap.name}", "DuelMediator")
                        trap.flip(True)
                        self._resolve_effect_tree(trap, source_card)
                        if trap.stats.data.icon.name == "NORMAL":
                            self.send_to_graveyard(trap)
                        did_activate = True
        return did_activate

    def check_game_over(self):
        if self.game_state.player_lp <= 0:
            self.on_game_over.emit("CPU")
        elif self.game_state.enemy_lp <= 0:
            self.on_game_over.emit("PLAYER")

    def _resolve_effect_tree(self, effect_card, trigger_source):
        from game.mechanics.context import EffectContext
        from game.mechanics.effect import Effect

        node = next((c for c in effect_card.children if isinstance(c, Effect)), None)
        if not node:
            return

        ctx = EffectContext(
            mediator=self,
            source_card=effect_card,
            player_board=self.game_state.player_board,
            enemy_board=self.game_state.enemy_board,
            event_trigger_card=trigger_source,
        )
        node.resolve(ctx)