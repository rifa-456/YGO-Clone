from typing import Optional, TYPE_CHECKING
from engine.scene.main.node import Node
from engine.scene.main.input import Input
from engine.logger import Logger
from game.scenes.duel.logic.turn_handler import TurnHandler
from .duel_scene_builder import DuelSceneBuilder
from .duel_scene_signals import DuelSceneSignals
from .input import DuelInputController
from .logic.duel_mediator import DuelMediator
from ...entities.card.card_state import CardState

if TYPE_CHECKING:
    from engine.scene.two_d.camera2D import Camera2D
    from engine.ui.containers.h_box_container import HBoxContainer
    from engine.ui.containers.v_box_container import VBoxContainer
    from engine.ui.buttons.button import Button
    from engine.ui.containers.center_container import CenterContainer
    from engine.ui.widgets.panel import Panel
    from engine.ui import Control
    from game.scenes.duel.hud.card_info import CardInfo
    from game.scenes.duel.hud.status_panel import StatusPanel
    from game.scenes.duel.hud.phase_bar import PhaseBar
    from game.entities.board.board import Board
    from game.entities.hand.hand import Hand
    from game.entities.deck.deck import Deck


class DuelScene(Node):
    def __init__(self) -> None:
        super().__init__("DuelScene")
        self.camera: Optional["Camera2D"] = None
        self.root_split: Optional["HBoxContainer"] = None

        self.card_panel: Optional["CardInfo"] = None
        self.game_zone: Optional["VBoxContainer"] = None
        self.status_panel: Optional["StatusPanel"] = None
        self.phase_bar: Optional["PhaseBar"] = None
        self._popup_layer: Optional["CenterContainer"] = None
        self._position_popup: Optional["Panel"] = None
        self._btn_attack: Optional["Button"] = None
        self._btn_defense: Optional["Button"] = None

        self._enemy_board_container: Optional["Control"] = None
        self._player_board_container: Optional["Control"] = None

        self.player_board: Optional["Board"] = None
        self.enemy_board: Optional["Board"] = None
        self.hand: Optional["Hand"] = None
        self.enemy_hand: Optional["Hand"] = None
        self.deck: Optional["Deck"] = None
        self.enemy_deck: Optional["Deck"] = None

        self.turn_handler = TurnHandler()
        self.mediator = DuelMediator()
        self.builder = DuelSceneBuilder(self)
        self.builder.build()
        self.signals = DuelSceneSignals(self)
        self.input_controller = DuelInputController(self)
        self.target_summon_state = CardState.FIELD_ATTACK

    def _ready(self) -> None:
        Logger.info("DuelScene Ready. Initializing systems...", "DuelScene")
        self.signals.wire_all()
        self.mediator.setup(
            self.turn_handler,
            self.player_board,
            self.enemy_board,
            self.hand,
            self.enemy_hand,
            self.deck.logic,
            self.enemy_deck.logic,
        )
        self.phase_bar.setup(self.turn_handler)
        self._connect_cross_board_navigation()
        self._start_game()

    def _input(self, event):
        """
        Global Input handling.
        Delegates manual inputs (like Q/E toggles) to the controller
        before handling global system actions.
        """
        self.input_controller.handle_manual_input(event)
        if Input.is_event_action(event, "ui_cancel"):
            Logger.info("Input: Action Cancelled", "DuelInput")
            self.input_controller.handle_cancel()

    def _start_game(self):
        Logger.info("Starting Duel...", "DuelScene")
        self.mediator.request_draw(self.deck.logic, amount=5)
        self.mediator.request_draw(self.enemy_deck.logic, amount=5)
        self.status_panel.refresh()
        self.hand.grab_focus()

    def _process(self, delta: float):
        if Input.is_action_just_pressed("debug_next_phase"):
            self.turn_handler.next_phase()

    def _connect_cross_board_navigation(self):
        """
        Links Player Board ↔ Enemy Board ↔ Hands for vertical navigation.
        """
        from engine.logger import Logger

        cols = self.player_board.logic.cols
        max_col_idx = cols - 1
        for visual_col in range(cols):
            player_logical_col = visual_col
            enemy_logical_col = max_col_idx - visual_col
            player_front = self.player_board.logic.get_slot(0, player_logical_col)
            enemy_front = self.enemy_board.logic.get_slot(0, enemy_logical_col)
            if player_front and enemy_front:
                player_front.focus_neighbor_top = player_front.get_path_to(enemy_front)
                enemy_front.focus_neighbor_bottom = enemy_front.get_path_to(player_front)
                Logger.debug(
                    f"Linked Player Slot[{0},{player_logical_col}] ↔ Enemy Slot[{0},{enemy_logical_col}]",
                    "DuelScene"
                )

        self.hand.connect_to_board(self.player_board, is_enemy=False)
        self.enemy_hand.connect_to_board(self.enemy_board, is_enemy=True)
        Logger.info("Cross-board navigation connected successfully", "DuelScene")
