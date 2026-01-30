import pygame
from typing import Optional, List, TYPE_CHECKING
from engine.logger import Logger
from engine.ui.enums import MouseFilter
from game.entities.card.card_state import CardState
from game.scenes.duel.logic.turn_handler import GamePhase
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.color import Color
from .input_state import DuelInputState
from game.entities.card.card_builder import CardVisualBuilder
from game.entities.card.card_visual_mode import CardVisualMode

if TYPE_CHECKING:
    from game.scenes.duel.duel_scene import DuelScene
    from game.entities.card import Card
    from game.entities.slot import Slot
    from game.entities.card.card_visuals import CardVisuals


class DuelInputController:

    def __init__(self, scene: "DuelScene"):
        self.scene = scene
        self.state = DuelInputState.IDLE
        self._selected_card: Optional["Card"] = None
        self._selected_slot: Optional["Slot"] = None
        self._tribute_buffer: List["Slot"] = []
        self._tribute_cost: int = 0

        self._ghost_visual: Optional["CardVisuals"] = None
        self._is_ghost_defense: bool = False

    def handle_hand_card_clicked(self, card: "Card") -> None:
        if self.state != DuelInputState.IDLE:
            return

        if self.scene.turn_handler.current_phase != GamePhase.MAIN:
            Logger.warn("Action Failed: Summoning only allowed in Main Phase.", "InputController")
            return

        if card.stats.data.card_type.name == "SPELL":
            Logger.info("Requesting Spell Activation...", "InputController")
            self.scene.mediator.activate_spell(card)
            self.scene.hand.remove_card(card)
            self.reset()
            return

        Logger.info(f"Input: Selected card {card.name} for Summoning.", "InputController")
        self._selected_card = card
        self._enter_ghost_mode(card)

    def handle_manual_input(self, event: pygame.event.Event) -> None:
        """
        Called by DuelScene._input to handle raw keyboard events (Q/E/ESC).
        """
        if self.state == DuelInputState.SUMMONING_GHOST:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_e:
                    self._is_ghost_defense = not self._is_ghost_defense
                    self._update_ghost_visuals()
                    Logger.info(f"Ghost Mode Toggled: {'DEF' if self._is_ghost_defense else 'ATK'}", "InputController")

                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self._selected_slot and not self._selected_slot.is_occupied():
                        self._confirm_ghost_summon()

    def handle_slot_clicked(self, slot: "Slot") -> None:
        """
        Routes slot interactions based on current state.
        """
        if self.state == DuelInputState.WAITING_FOR_TRIBUTE_SELECTION:
            self._handle_tribute_selection(slot)
            return

        if self.state == DuelInputState.SUMMONING_GHOST:
            if slot.is_occupied():
                Logger.warn("Invalid Selection: Slot occupied.", "InputController")
                return

            self._selected_slot = slot
            self._confirm_ghost_summon()
            return

        if slot.is_occupied():
            self.scene.signals.ui._update_hud_with_card(slot.card_node)
            slot.grab_focus()
        else:
            slot.grab_focus()

    def handle_cancel(self) -> None:
        """Resets input state to IDLE, handling Ghost Mode exit."""
        if self.state != DuelInputState.IDLE:
            Logger.info("Input: Action Cancelled", "InputController")

            if self.state == DuelInputState.SUMMONING_GHOST:
                self._exit_ghost_mode()

            self.reset()

    def _enter_ghost_mode(self, card: "Card"):
        """
        Sets up the visual ghost using the actual Board Slot as the parent.
        Targeting fixed to Row 0 (Monster Zone).
        """
        self._transition_to(DuelInputState.SUMMONING_GHOST)
        self._is_ghost_defense = False

        self._ghost_visual = CardVisualBuilder.build(CardVisualMode.FULL, card.stats.data)
        self._ghost_visual.name = "GhostCursor"
        self._ghost_visual.modulate = Color(1.0, 1.0, 1.0, 255.0 / 255.0)
        self._ghost_visual.mouse_filter = MouseFilter.IGNORE
        self._ghost_visual.z_index = 10

        TARGET_ROW = 0
        self.scene.player_board.set_row_isolation(TARGET_ROW, True)

        first_empty = self.scene.player_board.get_first_empty_slot(TARGET_ROW)
        target_slot = first_empty if first_empty else self.scene.player_board.get_slot(TARGET_ROW, 0)

        target_slot.grab_focus()
        self._selected_slot = target_slot

        viewport = self.scene.get_viewport()
        if not viewport.gui_focus_changed.is_connected(self._on_ghost_focus_changed):
            viewport.gui_focus_changed.connect(self._on_ghost_focus_changed)

        self._update_ghost_visuals()

    def _exit_ghost_mode(self):
        """
        Cleans up ghost visuals and restores board navigation.
        """
        if self._ghost_visual:
            if self._ghost_visual.get_parent():
                self._ghost_visual.get_parent().remove_child(self._ghost_visual)
            self._ghost_visual.queue_free()
            self._ghost_visual = None

        viewport = self.scene.get_viewport()
        if viewport.gui_focus_changed.is_connected(self._on_ghost_focus_changed):
            viewport.gui_focus_changed.disconnect(self._on_ghost_focus_changed)

        TARGET_ROW = 0
        self.scene.player_board.set_row_isolation(TARGET_ROW, False)
        self.scene.hand.connect_to_board(self.scene.player_board, is_enemy=False)

    def _on_ghost_focus_changed(self, control: "Control"):
        from game.entities.slot.slot import Slot
        if isinstance(control, Slot) and control.get_parent() == self.scene.player_board:
            self._selected_slot = control
            self._update_ghost_visuals()

    def _transition_to(self, new_state: DuelInputState) -> None:
        Logger.info(
            f"State Change: {self.state.name} -> {new_state.name}", "InputController"
        )
        self.state = new_state

    def _update_ghost_visuals(self):
        """
        Parents the ghost to the selected slot and injects the Slot's perspective geometry.
        """
        if not self._ghost_visual or not self._selected_slot:
            return

        if self._ghost_visual.get_parent() != self._selected_slot:
            if self._ghost_visual.get_parent():
                self._ghost_visual.get_parent().remove_child(self._ghost_visual)
            self._selected_slot.add_child(self._ghost_visual)

        target_rot = 90.0 if self._is_ghost_defense else 0.0
        self._ghost_visual.rotation_degrees = target_rot

        from engine.math.algorithms.geometry import Geometry2D

        slot_points = self._selected_slot._visual_poly_points
        if slot_points and len(slot_points) == 4:
            padding = 4.0
            offset_points = Geometry2D.offset_polygon(slot_points, padding)
            if offset_points:
                self._ghost_visual.position = Vector2(0, 0)
                t = self._ghost_visual.get_transform().affine_inverse()
                ghost_local_points = [t.xform(p) for p in offset_points]
                self._ghost_visual.set_quad_geometry(ghost_local_points)
                self._ghost_visual.set_face_up(not self._is_ghost_defense)

    def _confirm_ghost_summon(self):
        """
        Finalizes the summon based on ghost state.
        """
        if not self._selected_slot:
            return

        Logger.info(f"Input: Summon Confirmed (Defense={self._is_ghost_defense})", "InputController")

        target_state = CardState.FIELD_DEFENSE if self._is_ghost_defense else CardState.FIELD_ATTACK
        self.scene.target_summon_state = target_state
        self.scene.mediator.request_summon(self._selected_card, self._selected_slot)
        self._exit_ghost_mode()
        if self.state != DuelInputState.WAITING_FOR_TRIBUTE_SELECTION:
            self.reset()

    def reset(self) -> None:
        """
        Resets the Input Controller to its initial IDLE state.
        Clears all temporary selection buffers and ghost visuals.
        """
        Logger.info("Resetting Input State to IDLE", "InputController")

        self._exit_ghost_mode()

        self._selected_card = None
        self._selected_slot = None
        self._tribute_buffer.clear()
        self._tribute_cost = 0

        self._transition_to(DuelInputState.IDLE)