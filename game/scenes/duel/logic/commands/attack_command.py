from engine.logger import Logger
from game.mechanics.enums import EffectTrigger
from game.scenes.duel.logic.commands.base_command import DuelCommand
from game.scenes.duel.logic.turn_handler import GamePhase
from game.scenes.duel.logic.battle_handler import BattleHandler


class AttackCommand(DuelCommand):
    def __init__(self, attacker, defender):
        self.attacker = attacker
        self.defender = defender

    def execute(self, state, mediator):
        if state.turn_handler.current_phase != GamePhase.BATTLE:
            return

        Logger.info(
            f"Attack Declared: {self.attacker.name} -> {self.defender.name}",
            "AttackCommand",
        )
        mediator.on_attack_declared.emit(self.attacker, self.defender)
        trap_triggered = mediator.check_reactive_traps(
            EffectTrigger.ON_ATTACK, self.attacker
        )
        if trap_triggered:
            if not self.attacker.is_inside_tree() or (
                self.defender and not self.defender.is_inside_tree()
            ):
                Logger.info("Battle halted due to Trap Effect.", "AttackCommand")
                return

        result = BattleHandler.calculate_battle(self.attacker, self.defender)
        if result.damage_to_attacker > 0:
            state.player_lp -= result.damage_to_attacker
            Logger.info(
                f"Player took {result.damage_to_attacker} dmg.", "AttackCommand"
            )

        if result.damage_to_defender > 0:
            state.enemy_lp -= result.damage_to_defender
            Logger.info(f"Enemy took {result.damage_to_defender} dmg.", "AttackCommand")

        mediator.on_stats_changed.emit(state.player_lp, state.enemy_lp)
        for dead_card in result.destroyed_cards:
            mediator.send_to_graveyard(dead_card)

        mediator.check_game_over()
