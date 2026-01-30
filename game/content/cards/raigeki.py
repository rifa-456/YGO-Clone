from typing import TYPE_CHECKING
from game.mechanics.effect import Effect
from game.mechanics.enums import GameGroups
from engine.logger import Logger

if TYPE_CHECKING:
    from game.entities.card.card import Card


class RaigekiEffect(Effect):
    def resolve(self, context):
        targets = [
            node
            for node in self.get_tree().get_nodes_in_group(GameGroups.ENEMY_MONSTERS)
            if isinstance(node, Card)
        ]
        if not targets:
            Logger.info("No targets found.", "Raigeki")
            return

        Logger.info(f"Destroying {len(targets)} monsters.", "Raigeki")
        for monster in list(targets):
            context.arbiter.send_to_graveyard(monster)


def setup(card: "Card"):
    effect_node = RaigekiEffect("RaigekiLogic")
    card.add_child(effect_node)
