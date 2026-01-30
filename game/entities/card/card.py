from typing import Optional
from engine.scene.main.signal import Signal
from engine.ui.control import Control
from engine.ui.enums import FocusMode, SizeFlag
from engine.math.datatypes.vector2 import Vector2
from engine.scene.main.input import Input
from .card_builder import CardVisualBuilder
from .card_logic import CardLogic
from .card_state import CardState
from .card_stats import CardStats
from .card_visual_mode import CardVisualMode
from game.autoload.card_database import CardData
from ...autoload.script_loader import ScriptLoader


class Card(Control):
    CARD_WIDTH = 128
    CARD_ASPECT_RATIO = 1.45
    CARD_HEIGHT = int(CARD_WIDTH * CARD_ASPECT_RATIO)

    KEY_CARD_BACK = "assets/cards/back.png"

    State = CardState
    on_selected = Signal("on_selected")

    def __init__(self, data: CardData, name: Optional[str] = None):
        super().__init__(name if name else f"Card_{data.id}")
        self.custom_minimum_size = Vector2(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.focus_mode = FocusMode.ALL
        self.size_flags_horizontal = SizeFlag.SHRINK_CENTER
        self.size_flags_vertical = SizeFlag.SHRINK_CENTER
        self.logic = CardLogic()
        self.stats = CardStats(data)
        self.visuals = CardVisualBuilder().build(CardVisualMode.HAND, data)
        self.add_child(self.visuals)
        self.logic.on_state_changed.connect(self._on_logic_state_changed)
        self.logic.on_flip.connect(self._on_logic_flip)
        ScriptLoader.apply_script(self)
        self._sync_visuals()

    def set_visual_mode(self, mode: CardVisualMode):
        """
        Rebuilds the visuals for a specific context (e.g. moving from Hand to Field).
        """
        if self.visuals:
            if self.visuals.is_inside_tree():
                self.visuals.queue_free()
            else:
                self.remove_child(self.visuals)

        self.visuals = CardVisualBuilder().build(mode, self.stats.data)
        self.add_child(self.visuals)
        self._sync_visuals()

    def _notification(self, what: int) -> None:
        super()._notification(what)
        if what == Control.NOTIFICATION_FOCUS_ENTER:
            self.z_index = 10
        elif what == Control.NOTIFICATION_FOCUS_EXIT:
            self.z_index = 0

    def _gui_input(self, event):
        """
        Input Handling (Tier 1 Responsibility).
        Captures input and emits high-level signals.
        """
        super()._gui_input(event)
        if Input.is_event_action(event, "ui_accept"):
            self.on_selected.emit(self)
            self.accept_event()

    def flip(self, face_up: bool):
        """Facade method to modify internal logic."""
        self.logic.flip(face_up)

    def set_state(self, state: CardState):
        """Facade method to modify internal logic."""
        self.logic.set_state(state)

    def _on_logic_state_changed(self, new_state: CardState):
        """
        Reacts to Logic changes.
        Authority decides how this affects the Visuals.
        """
        is_defense = new_state == CardState.FIELD_DEFENSE
        self.visuals.set_orientation(is_defense)
        self.visuals.set_face_up(self.logic.face_up)

    def _on_logic_flip(self, face_up: bool):
        self.visuals.set_face_up(face_up)

    def _sync_visuals(self):
        """Forces a refresh of visuals based on current logic."""
        is_defense = self.logic.current_state == CardState.FIELD_DEFENSE
        self.visuals.set_orientation(is_defense)
        self.visuals.set_face_up(self.logic.face_up)

    def set_quad_geometry(self, points: list[Vector2]):
        """
        Injects specific screen-space geometry for this card.
        Used by Slots to render the card in perspective.
        """
        self.position = Vector2(0, 0)
        self.rotation = 0
        self.visuals.set_quad_geometry(points)

    def reset_visual_transform(self):
        """Resets the card to standard UI rendering (e.g. returning to hand)."""
        self.visuals.reset_geometry()
