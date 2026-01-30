from typing import TYPE_CHECKING, Optional
from engine.math.datatypes.vector2 import Vector2
from engine.ui.widgets import Panel, Label
from engine.ui.containers import HBoxContainer, MarginContainer
from engine.ui.enums import SizeFlag, LayoutPreset

if TYPE_CHECKING:
    from game.scenes.duel.logic.game_state import GameState


class StatusPanel(Panel):
    """
    Top bar displaying Life Points (LP) and Turn count.
    """

    def __init__(self, name: str = "DuelStatusPanel"):
        super().__init__(name=name)
        self.custom_minimum_size = Vector2(0, 60)
        self.size_flags_horizontal = SizeFlag.EXPAND_FILL
        self._lbl_player_lp: Label
        self._lbl_turn: Label
        self._lbl_enemy_lp: Label
        self.game_state: Optional["GameState"] = None
        self._build_ui()

    def _build_ui(self):
        margin = MarginContainer("StatusMargin")
        margin.set_anchors_preset(LayoutPreset.FULL_RECT)
        margin.add_constant_override("margin_left", 20)
        margin.add_constant_override("margin_right", 20)
        margin.add_constant_override("margin_top", 10)
        margin.add_constant_override("margin_bottom", 10)
        self.add_child(margin)
        hbox = HBoxContainer(separation=50, name="StatusHBox")
        hbox.size_flags_horizontal = SizeFlag.EXPAND_FILL
        margin.add_child(hbox)
        self._lbl_player_lp = Label("LP ????", name="LblPlayer")
        self._lbl_player_lp.size_flags_horizontal = SizeFlag.EXPAND
        self._lbl_player_lp.add_theme_color_override(
            "font_color", self.get_theme_color("text_player", "Label")
        )
        hbox.add_child(self._lbl_player_lp)
        self._lbl_turn = Label("TURN ?", name="LblTurn")
        self._lbl_turn.size_flags_horizontal = SizeFlag.EXPAND
        self._lbl_turn.add_theme_color_override(
            "font_color", self.get_theme_color("text_highlight", "Label")
        )
        hbox.add_child(self._lbl_turn)
        self._lbl_enemy_lp = Label("CPU LP ????", name="LblEnemy")
        self._lbl_enemy_lp.size_flags_horizontal = SizeFlag.EXPAND
        self._lbl_enemy_lp.add_theme_color_override(
            "font_color", self.get_theme_color("text_enemy", "Label")
        )
        hbox.add_child(self._lbl_enemy_lp)

    def assign_game_state(self, game_state: "GameState"):
        """
        Injects the GameState dependency and performs the first refresh.
        """
        self.game_state = game_state
        self.refresh()

    def on_turn_started(self):
        """
        Triggered by the 'on_turn_start' signal.
        Ignores signal arguments and pulls fresh data from GameState.
        """
        self.refresh()

    def on_stats_changed(self):
        """
        Triggered by the 'on_turn_start' signal.
        Ignores signal arguments and pulls fresh data from GameState.
        """
        self.refresh()

    def refresh(self):
        """
        Pulls the latest LP and Turn data from the GameState.
        """
        if not self.game_state:
            return

        self._set_lp(self.game_state.player_lp, self.game_state.enemy_lp)
        if self.game_state:
            current_turn = getattr(self.game_state.turn_handler, "turn_count", 1)
            self._set_turn(current_turn)

    def _set_lp(self, player: int, enemy: int):
        self._lbl_player_lp.set_text(f"LP {player}")
        self._lbl_enemy_lp.set_text(f"CPU LP {enemy}")

    def _set_turn(self, turn: int):
        self._lbl_turn.set_text(f"TURN {turn}")
