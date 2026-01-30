from engine.ui.widgets import TextureRect
from engine.ui.control import Control
from engine.ui.enums import LayoutPreset, MouseFilter
from game.autoload.card_database import CardData
from .card_visual_mode import CardVisualMode
from .card_visuals import CardVisuals
from ...autoload.texture_registry import TextureRegistry


class CardVisualBuilder:
    @staticmethod
    def build(mode: CardVisualMode, data: CardData = None) -> CardVisuals:
        """
        Constructs the CardVisuals node.
        """
        visuals = CardVisuals(mode)

        tex_back = TextureRegistry.get("assets/cards/back.png")
        tex_front = TextureRegistry.get(data.texture_path) if data else None

        back = TextureRect(tex_back, "Back")
        back.set_anchors_preset(LayoutPreset.FULL_RECT)
        back.mouse_filter = MouseFilter.IGNORE
        back.stretch_mode = True
        back.expand_mode = True
        visuals.add_child(back)
        visuals.back_rect = back

        front_container = Control("FrontContainer")
        front_container.set_anchors_preset(LayoutPreset.FULL_RECT)
        front_container.mouse_filter = MouseFilter.IGNORE
        visuals.add_child(front_container)

        if mode in [CardVisualMode.FULL, CardVisualMode.HAND]:
            if data and tex_front:
                front = TextureRect(tex_front, "Front")
                front.set_anchors_preset(LayoutPreset.FULL_RECT)
                front.mouse_filter = MouseFilter.IGNORE
                front.stretch_mode = True
                front.expand_mode = True
                front_container.add_child(front)
                visuals.front_rect = front

        visuals.set_face_up(True)
        return visuals
