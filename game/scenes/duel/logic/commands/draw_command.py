from typing import Optional
from engine.logger import Logger
from game.entities.deck.deck_logic import DeckLogic
from game.scenes.duel.logic.commands.base_command import DuelCommand
from game.scenes.duel.logic.turn_handler import TurnOwner


class DrawCommand(DuelCommand):
    def __init__(self, target_deck: Optional[DeckLogic] = None, amount: int = 1):
        self.target_deck = target_deck
        self.amount = amount

    def execute(self, state, mediator):
        if self.target_deck:
            deck_to_use = self.target_deck
        else:
            is_turn_player = state.turn_handler.current_turn_owner == TurnOwner.PLAYER
            deck_to_use = state.player_deck if is_turn_player else state.enemy_deck

        is_player_drawing = (deck_to_use == state.player_deck)
        owner_str = "PLAYER" if is_player_drawing else "ENEMY"
        Logger.info(f"Processing Draw for {owner_str} (Amount: {self.amount}).", "DrawCommand")
        for _ in range(self.amount):
            card_data = deck_to_use.pop_card()
            if card_data:
                mediator.draw_approved.emit(card_data, is_player_drawing)
            else:
                mediator.draw_failed.emit("Deck Empty")
                Logger.warn(f"Draw failed for {owner_str}: Deck Empty.", "DrawCommand")
                break
