import pygame
import sys
from typing import Callable, Optional
from engine.math.datatypes.vector2 import Vector2
from engine.servers.rendering.rendering_server import RenderingServer
from engine.scene.main.input import Input
from engine.logger import Logger
from engine.graphics.formats import log_format_details


class PygameDisplayServer:
    """
    Manages the OS Window (Pygame Surface) and the Main Loop.
    Strictly handles window context creation. Drawing is delegated to the RenderingServer.
    """

    def __init__(self, title: str = "YGO Engine", size: Vector2 = Vector2(800, 600)):
        Logger.info(
            f"Initializing Display Server: {title} ({size.x}x{size.y})", "DisplayServer"
        )

        log_format_details()

        status = pygame.init()
        if status[1] > 0:
            Logger.warn(f"Pygame initialized with {status[1]} errors.", "DisplayServer")

        self.window_size = size

        flags = pygame.DOUBLEBUF

        self.screen = pygame.display.set_mode((int(size.x), int(size.y)), flags)
        pygame.display.set_caption(title)

        self.clock = pygame.time.Clock()
        self.running = True

        self.rendering_server = RenderingServer.get_singleton()
        self.rendering_server.set_display_window(self.screen)

        self.input = Input.get_singleton()
        self._event_callback: Optional[Callable[[pygame.event.Event], None]] = None
        Logger.info("Display Server initialized successfully.", "DisplayServer")

    def set_event_dispatch(self, callback: Callable[[pygame.event.Event], None]):
        """
        Registers a callback to receive raw events (usually SceneTree.root.push_input).
        """
        self._event_callback = callback

    def process_events(self):
        self.input.flush_buffered_events()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                Logger.info("Quit event received. Shutting down.", "DisplayServer")
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self._handle_resize(event.w, event.h)
            self.input.parse_input_event(event)
            if self._event_callback:
                self._event_callback(event)

    def _handle_resize(self, width: int, height: int):
        self.window_size = Vector2(width, height)
        self.screen = pygame.display.set_mode(
            (width, height), pygame.RESIZABLE | pygame.DOUBLEBUF
        )
        self.rendering_server.set_display_window(self.screen)

    def get_delta_time(self) -> float:
        return self.clock.tick(60) / 1000.0

    @staticmethod
    def swap_buffers():
        pygame.display.flip()

    @staticmethod
    def close():
        Logger.info("Closing Display Server.", "DisplayServer")
        pygame.quit()
        sys.exit()