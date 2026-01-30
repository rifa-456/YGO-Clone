import pygame
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from engine.drivers.pygame.display_server import PygameDisplayServer
from engine.scene.main.input import Input
from engine.scene.main.scene_tree import SceneTree
from engine.logger import Logger
from engine.ui.theme import Theme, StyleBoxFlat, StyleBoxTexture
from game.autoload.card_database import load_resources
from game.autoload.settings import Settings
from game.autoload.texture_registry import TextureRegistry
from game.scenes.duel.duel_scene import DuelScene


def setup_input():
    Input.register_action("ui_up", [pygame.K_UP])
    Input.register_action("ui_down", [pygame.K_DOWN])
    Input.register_action("ui_left", [pygame.K_LEFT])
    Input.register_action("ui_right", [pygame.K_RIGHT])
    Input.register_action("ui_accept", [pygame.K_z, pygame.K_RETURN])
    Input.register_action("ui_cancel", [pygame.K_x, pygame.K_BACKSPACE])
    Input.register_action("ui_focus_next", [pygame.K_SPACE])
    Input.register_action("ui_rotate_left", [pygame.K_q])
    Input.register_action("ui_rotate_right", [pygame.K_e])
    Input.register_action("debug_next_phase", [pygame.K_TAB])
    Input.register_action("debug_toggle", [pygame.K_F1])
    Input.register_action("debug_dump", [pygame.K_p])
    pygame.key.set_repeat(400, 50)


def setup_theme():
    theme = Theme.get_default()

    theme.set_font("main_font", "Global", pygame.font.SysFont("Arial", 16))
    theme.set_font("body_font", "Label", pygame.font.SysFont("Arial", 14))

    theme.set_font("header_font", "Label", pygame.font.SysFont("Arial", 20, bold=True))
    theme.set_font("bold_font", "Label", pygame.font.SysFont("Arial", 14, bold=True))

    def c(r, g, b, a=255):
        return Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

    theme.set_color("panel_bg", "Panel", c(30, 30, 30, 200))
    theme.set_color("ui_bg", "Editor", c(20, 20, 20))
    theme.set_color("ui_border", "Editor", c(60, 60, 60))
    theme.set_color("text_normal", "Label", c(220, 220, 220))
    theme.set_color("text_highlight", "Label", c(255, 215, 0))
    theme.set_color("text_player", "Label", c(100, 150, 255))
    theme.set_color("text_enemy", "Label", c(255, 100, 100))

    style_info = StyleBoxFlat()
    style_info.bg_color = c(20, 20, 20, 230)
    style_info.border_color = c(60, 60, 60)
    style_info.border_width = 1
    theme.set_stylebox("panel", "CardInfoPanel", style_info)

    style_grey = StyleBoxFlat()
    style_grey.bg_color = c(30, 30, 30)
    theme.set_stylebox("panel", "Panel", style_grey)

    style_empty = StyleBoxFlat()
    style_empty.bg_color = c(0, 0, 0, 0)
    theme.set_stylebox("panel", "GameSurface", style_empty)

    theme.set_font(
        "phase_font", "PhaseBar", pygame.font.SysFont("Arial", 16, bold=True)
    )
    theme.set_font(
        "status_font", "DuelStatusBox", pygame.font.SysFont("Arial", 22, bold=True)
    )


def main():
    Logger.info("Starting YGO Clone...", "Main")
    display_server = PygameDisplayServer(
        title=Settings.TITLE,
        size=Vector2(Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
    )
    TextureRegistry.initialize()
    load_resources()
    setup_input()
    setup_theme()

    duel_scene = DuelScene()

    scene_tree = SceneTree(
        root_node=duel_scene,
        display_window_size=Vector2(Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
    )

    display_server.set_event_dispatch(scene_tree.root.push_input)

    if hasattr(duel_scene, "camera"):
        scene_tree.current_camera = duel_scene.camera

    Logger.info("Starting Game Loop.", "Main")

    while display_server.running:
        display_server.process_events()

        dt = display_server.get_delta_time()
        scene_tree.process(dt)

        scene_tree.render()

        display_server.swap_buffers()

    display_server.close()


if __name__ == "__main__":
    main()