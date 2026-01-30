import importlib
import re
from typing import TYPE_CHECKING
from engine.logger import Logger

if TYPE_CHECKING:
    from game.entities.card.card import Card

CONTENT_PACKAGE = "game.content.cards"


class ScriptLoader:
    """
    Bridge between Engine and Content.
    Refactored to load scripts based on snake_case card names rather than IDs.
    Example: "Blue-Eyes White Dragon" -> "blue_eyes_white_dragon.py"
    """

    @staticmethod
    def apply_script(card: "Card") -> None:
        """
        Attempts to find and run a setup script for the given card.
        """
        raw_name = card.stats.data.name
        safe_name = re.sub(
            r"[^a-z0-9_]", "", raw_name.lower().replace(" ", "_").replace("-", "_")
        )
        module_name = safe_name

        try:
            module = importlib.import_module(f"{CONTENT_PACKAGE}.{module_name}")
            if hasattr(module, "setup"):
                Logger.info(
                    f"Applying script: {module_name} for '{raw_name}'", "ScriptLoader"
                )
                module.setup(card)
            else:
                Logger.warn(
                    f"Script {module_name} loaded but missing 'setup(card)' function.",
                    "ScriptLoader",
                )

        except ImportError:
            pass
        except Exception as e:
            Logger.error(
                f"Failed to load script '{module_name}' for card '{raw_name}': {e}",
                "ScriptLoader",
            )
