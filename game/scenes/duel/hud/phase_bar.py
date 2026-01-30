from typing import Dict, Optional, Tuple
from engine.core.textures.texture import Texture
from engine.ui.control import LayoutPreset
from engine.ui.containers.panel_container import PanelContainer
from engine.ui.containers.h_box_container import HBoxContainer
from engine.ui.widgets.texture_rect import TextureRect
from engine.ui.theme import StyleBoxTexture
from engine.core.resource_loader import ResourceLoader
from engine.math.datatypes.vector2 import Vector2
from game.scenes.duel.logic.turn_handler import GamePhase, TurnOwner, TurnHandler


class PhaseIndicator(TextureRect):
    """
    A specific TextureRect that swaps its texture based on the current
    Turn Owner and Phase State.
    """

    TEX_PLAYER_ON = "assets/ui/phase_box_player_on.png"
    TEX_PLAYER_OFF = "assets/ui/phase_box_player_off.png"
    TEX_ENEMY_ON = "assets/ui/phase_box_enemy_on.png"
    TEX_ENEMY_OFF = "assets/ui/phase_box_enemy_off.png"

    def __init__(self, name: str):
        super().__init__(name=name)
        self.stretch_mode = False
        self._textures: Dict[str, Optional[Texture]] = {
            "p_on": ResourceLoader.load(self.TEX_PLAYER_ON, Texture),
            "p_off": ResourceLoader.load(self.TEX_PLAYER_OFF, Texture),
            "e_on": ResourceLoader.load(self.TEX_ENEMY_ON, Texture),
            "e_off": ResourceLoader.load(self.TEX_ENEMY_OFF, Texture),
        }
        self.texture = self._textures["p_off"]

    def update_state(self, is_active: bool, is_player_turn: bool) -> None:
        prefix = "p_" if is_player_turn else "e_"
        suffix = "on" if is_active else "off"
        key = f"{prefix}{suffix}"

        if key in self._textures and self._textures[key]:
            self.texture = self._textures[key]


class PhaseBar(PanelContainer):
    """
    Displays the current phase of the duel using a styled container.
    """

    BG_PATH = "assets/ui/phase_bar.png"

    def __init__(self, name: str = "PhaseBar"):
        super().__init__(name=name)

        self.set_anchors_preset(LayoutPreset.CENTER)
        self._setup_style()
        self.container = HBoxContainer(separation=2, name="PhaseSlots")
        self.add_child(self.container)

        self.indicators: Dict[GamePhase, PhaseIndicator] = {}
        self._setup_indicators()

        self._current_phase = GamePhase.DRAW
        self._is_player_turn = True

    def _setup_style(self):
        style = StyleBoxTexture()
        style.texture = ResourceLoader.load(self.BG_PATH, Texture)
        style.content_margin_left = 12
        style.content_margin_right = 12
        style.content_margin_top = 8
        style.content_margin_bottom = 8
        self.add_theme_stylebox_override("panel", style)

    def _setup_indicators(self):
        phase_map: list[Tuple[GamePhase, str]] = [
            (GamePhase.DRAW, "DP"),
            (GamePhase.MAIN, "MP"),
            (GamePhase.BATTLE, "BP"),
            (GamePhase.END, "EP"),
        ]

        for phase, short_name in phase_map:
            indicator = PhaseIndicator(f"Ind_{short_name}")
            self.container.add_child(indicator)
            self.indicators[phase] = indicator

    def setup(self, turn_handler: "TurnHandler") -> None:
        turn_handler.on_phase_change.connect(self._on_phase_change)
        turn_handler.on_turn_owner_changed.connect(self._on_turn_owner_change)
        self._current_phase = turn_handler.current_phase
        self._is_player_turn = turn_handler.current_turn_owner == TurnOwner.PLAYER
        self._refresh_visuals()

    def _on_phase_change(self, new_phase: GamePhase) -> None:
        self._current_phase = new_phase
        self._refresh_visuals()

    def _on_turn_owner_change(self, new_owner: TurnOwner) -> None:
        self._is_player_turn = new_owner == TurnOwner.PLAYER
        self._refresh_visuals()

    def _refresh_visuals(self) -> None:
        for phase, indicator in self.indicators.items():
            is_active = phase == self._current_phase
            indicator.update_state(is_active, self._is_player_turn)

    def _notification(self, what: int) -> None:
        super()._notification(what)
        if what == self.NOTIFICATION_ENTER_TREE or what == self.NOTIFICATION_RESIZED:
            self._update_position_perspective()

    def _update_position_perspective(self):
        """
        Locates the DuelTable and asks for the screen coordinate of the exact center.
        """
        parent = self.get_parent()
        if not parent:
            return

        duel_table = None
        for child in parent.children:
            if child.name == "DuelTable":
                duel_table = child
                break

        if not duel_table or not hasattr(duel_table, "transform_point"):
            return

        logical_size = duel_table.get_logical_size()
        center_x_logical = logical_size.x / 2.0
        center_y_logical = logical_size.y / 2.0

        center_screen = duel_table.transform_point(
            Vector2(center_x_logical, center_y_logical)
        )

        w = self.size.x
        h = self.size.y
        final_x = center_screen.x - (w / 2)
        final_y = center_screen.y - (h / 2)

        self.position = Vector2(final_x, final_y)
