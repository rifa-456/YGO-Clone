from typing import Optional, TYPE_CHECKING
from engine.scene.main.node import Node
from engine.logger import Logger

if TYPE_CHECKING:
    from game.entities.card.card import Card
    from game.mechanics.context import EffectContext


class Effect(Node):
    """
    Base component for all Card Effects.
    Must be attached as a child of a Card entity.
    """

    def __init__(self, name: str = "Effect") -> None:
        super().__init__(name)
        self.card: Optional["Card"] = None

    def _ready(self) -> None:
        parent = self.parent
        from game.entities.card.card import Card

        if not isinstance(parent, Card):
            Logger.warn(
                f"Effect '{self.name}' attached to non-Card parent.", "EffectSystem"
            )
            return
        self.card = parent

    def resolve(self, context: "EffectContext") -> None:
        """
        Execute the effect logic.
        Override this in subclasses.
        """
        pass
