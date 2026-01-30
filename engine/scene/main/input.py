import pygame
from typing import Dict, List, Set, Optional
from engine.logger import Logger  # Added for debugging


class Input:
    """
    Singleton Input Manager.
    Maps raw input events to Actions.
    """

    _instance: Optional["Input"] = None

    _actions: Dict[str, List[int]] = {}

    _pressed_keys: Set[int] = set()
    _just_pressed_keys: Set[int] = set()
    _just_released_keys: Set[int] = set()

    _mouse_position: tuple[int, int] = (0, 0)
    _mouse_buttons: Set[int] = set()
    _just_pressed_mouse: Set[int] = set()
    _just_released_mouse: Set[int] = set()

    @staticmethod
    def get_singleton():
        if Input._instance is None:
            Input._instance = Input()
        return Input._instance

    @staticmethod
    def register_action(action_name: str, key_codes: List[int]):
        """Maps an action name (e.g., 'ui_left') to a list of keycodes."""
        if action_name not in Input._actions:
            Input._actions[action_name] = []
        Input._actions[action_name].extend(key_codes)

    @staticmethod
    def flush_buffered_events():
        """
        Called once per frame BEFORE the event loop.
        Clears the 'just' states for the new frame.
        """
        Input._just_pressed_keys.clear()
        Input._just_released_keys.clear()
        Input._just_pressed_mouse.clear()
        Input._just_released_mouse.clear()

    @staticmethod
    def parse_input_event(event: pygame.event.Event):
        """
        Feeds a raw Pygame event into the manager.
        """
        if event.type == pygame.KEYDOWN:
            Input._pressed_keys.add(event.key)
            Input._just_pressed_keys.add(event.key)

        elif event.type == pygame.KEYUP:
            if event.key in Input._pressed_keys:
                Input._pressed_keys.remove(event.key)
            Input._just_released_keys.add(event.key)

        elif event.type == pygame.MOUSEMOTION:
            Input._mouse_position = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            Input._mouse_buttons.add(event.button)
            Input._just_pressed_mouse.add(event.button)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in Input._mouse_buttons:
                Input._mouse_buttons.remove(event.button)
            Input._just_released_mouse.add(event.button)

    @staticmethod
    def is_action_pressed(action_name: str) -> bool:
        keys = Input._actions.get(action_name, [])
        for key in keys:
            if key in Input._pressed_keys:
                return True
        return False

    @staticmethod
    def is_action_just_pressed(action_name: str) -> bool:
        keys = Input._actions.get(action_name, [])
        for key in keys:
            if key in Input._just_pressed_keys:
                return True
        return False

    @staticmethod
    def is_action_just_released(action_name: str) -> bool:
        keys = Input._actions.get(action_name, [])
        for key in keys:
            if key in Input._just_released_keys:
                return True
        return False

    @staticmethod
    def is_event_action(event: pygame.event.Event, action_name: str) -> bool:
        """
        Checks if the provided raw event matches the action.
        Useful for _input(event) callbacks.
        """
        if action_name not in Input._actions:
            return False

        accepted_keys = Input._actions[action_name]
        is_match = False

        if event.type == pygame.KEYDOWN:
            is_match = event.key in accepted_keys
        elif event.type == pygame.MOUSEBUTTONDOWN:
            is_match = event.button in accepted_keys

        return is_match

    @staticmethod
    def get_mouse_position() -> tuple[int, int]:
        return Input._mouse_position