import os
from typing import TYPE_CHECKING
from engine.scene.two_d.camera2D import Camera2D
from engine.ui import CenterContainer
from engine.ui.containers.h_box_container import HBoxContainer
from engine.ui.containers.margin_container import MarginContainer
from engine.ui.control import LayoutPreset, SizeFlag, MouseFilter, Control, GrowDirection
from engine.logger import Logger
from game.autoload.texture_registry import TextureRegistry
from game.entities.hand.hand import Hand
from game.entities.deck.deck import Deck
from game.scenes.duel.hud.card_info import CardInfo
from game.scenes.duel.hud.status_panel import StatusPanel
from game.scenes.duel.hud.phase_bar import PhaseBar
from game.entities.board.board import Board
from game.entities.board.duel_table import DuelTable
from game.resources.deck_loader import DeckRepository
from engine.ui.widgets.texture_rect import TextureRect

if TYPE_CHECKING:
    from game.scenes.duel.duel_scene import DuelScene


class DuelSceneBuilder:
    """
    Constructs the visual scene tree for the DuelScene.
    """

    def __init__(self, scene: "DuelScene") -> None:
        self.scene = scene

    def build(self) -> None:
        Logger.info("Building DuelScene tree...", "DuelSceneBuilder")
        self._build_camera()

        self._build_background()

        self._build_ui_root()

        self._build_left_panel()

        self._build_game_zone()

        self._build_boards()
        self._build_decks()

        Logger.info("DuelScene tree built successfully.", "DuelSceneBuilder")

    def _build_camera(self) -> None:
        self.scene.camera = Camera2D("MainCam")
        self.scene.add_child(self.scene.camera)

    def _build_background(self) -> None:
        """
        Creates the global background texture that covers the entire window.
        """
        bg = TextureRect(name="GlobalBackground")
        bg.texture = TextureRegistry.get("assets/board/board_bg.png")
        bg.set_anchors_preset(LayoutPreset.FULL_RECT)
        bg.expand_mode = True
        bg.stretch_mode = True
        self.scene.add_child(bg)

    def _build_ui_root(self) -> None:
        self.scene.root_split = HBoxContainer(separation=0, name="RootSplit")
        self.scene.root_split.set_anchors_preset(LayoutPreset.FULL_RECT)
        self.scene.add_child(self.scene.root_split)

    def _build_left_panel(self) -> None:
        self.scene.card_panel = CardInfo()
        self.scene.root_split.add_child(self.scene.card_panel)

    def _build_game_zone(self) -> None:
        self.scene.game_zone = Control(name="GameZone")
        self.scene.game_zone.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self.scene.game_zone.size_flags_vertical = SizeFlag.EXPAND_FILL
        self.scene.game_zone.set_anchors_preset(LayoutPreset.FULL_RECT)

        self.scene.root_split.add_child(self.scene.game_zone)

        self._build_status_panel()
        self._build_phase_bar()
        self._build_enemy_hand_area()
        self._build_hand_area()

    def _build_enemy_hand_area(self) -> None:
        """
        Constructs the Enemy Hand area anchored to the top.
        """
        self.scene.enemy_hand = Hand(
            name="EnemyHand",
            scale=0.35,
            interaction_enabled=False
        )

        container = CenterContainer("EnemyHandCenter")
        container.set_anchors_preset(LayoutPreset.TOP_WIDE)
        container.mouse_filter = MouseFilter.IGNORE
        container.offset_top = 80
        container.offset_left = 490
        container.add_child(self.scene.enemy_hand)
        self.scene.game_zone.add_child(container)

    def _build_status_panel(self) -> None:
        self.scene.status_panel = StatusPanel()
        self.scene.status_panel.set_anchors_preset(LayoutPreset.TOP_WIDE)
        self.scene.status_panel.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self.scene.game_zone.add_child(self.scene.status_panel)

    def _build_phase_bar(self) -> None:
        self.scene.phase_bar = PhaseBar()
        self.scene.game_zone.add_child(self.scene.phase_bar)

    def _build_boards(self) -> None:
        """
        Instantiates the DuelTable and the logical boards.
        """
        self.scene.duel_table = DuelTable("DuelTable")
        self.scene.game_zone.add_child(self.scene.duel_table)
        self.scene.player_board = Board(False, "PlayerBoard")
        self.scene.enemy_board = Board(True, "EnemyBoard")
        self.scene.duel_table.add_child(self.scene.player_board)
        self.scene.duel_table.add_child(self.scene.enemy_board)

    def _build_hand_area(self) -> None:
        self.scene.hand = Hand("PlayerHand")
        container = CenterContainer("PlayerHandCenter")
        container.set_anchors_preset(LayoutPreset.BOTTOM_WIDE)
        container.grow_vertical = GrowDirection.BEGIN
        container.mouse_filter = MouseFilter.IGNORE
        margin = MarginContainer("Margin")
        margin.add_constant_override("margin_bottom", 20)
        margin.add_child(self.scene.hand)
        container.add_child(margin)
        self.scene.game_zone.add_child(container)

    def _build_decks(self) -> None:
        player_deck_path = os.path.join("game", "resources", "player_deck.json")
        player_deck_cards = DeckRepository.load_deck(player_deck_path)
        self.scene.deck = Deck(player_deck_cards, "PlayerDeck")
        if self.scene.player_board.deck_slot:
            self.scene.player_board.deck_slot.assign_card(self.scene.deck)

        ai_deck_path = os.path.join("game", "resources", "ai_deck.json")
        enemy_deck_cards = DeckRepository.load_deck(ai_deck_path)
        if not enemy_deck_cards:
            enemy_deck_cards = list(player_deck_cards)
        self.scene.enemy_deck = Deck(enemy_deck_cards, "EnemyDeck")
        if self.scene.enemy_board.deck_slot:
            self.scene.enemy_board.deck_slot.assign_card(self.scene.enemy_deck)