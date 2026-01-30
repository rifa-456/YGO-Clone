from engine.scene.main.signal import Signal
from engine.logger import Logger
from .card_state import CardState


class CardLogic:
    def __init__(self):
        self.current_state: CardState = CardState.HAND
        self.face_up: bool = True

        self.on_state_changed = Signal("on_state_changed")
        self.on_flip = Signal("on_flip")

    def set_state(self, new_state: CardState):
        """Transitions the card to a new gameplay state."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            Logger.info(
                f"State transition: {old_state.name} -> {new_state.name}", "CardLogic"
            )
            self.on_state_changed.emit(new_state)

    def flip(self, face_up: bool):
        """Sets the face-up status."""
        if self.face_up != face_up:
            self.face_up = face_up
            self.on_flip.emit(face_up)

    def is_on_field(self) -> bool:
        return self.current_state in (CardState.FIELD_ATTACK, CardState.FIELD_DEFENSE)
