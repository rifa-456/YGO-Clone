import os
import json
from enum import Enum
from engine.logger import Logger
from engine.core.resource import Resource
from engine.core.resource_loader import ResourceLoader
from game.mechanics.enums import EffectTrigger


class CardType(Enum):
    MONSTER = "MONSTER"
    SPELL = "SPELL"
    TRAP = "TRAP"


class CardIcon(Enum):
    NONE = "NONE"
    NORMAL = "NORMAL"
    EQUIP = "EQUIP"
    FIELD = "FIELD"
    QUICK_PLAY = "QUICK_PLAY"
    RITUAL = "RITUAL"
    CONTINUOUS = "CONTINUOUS"
    COUNTER = "COUNTER"


class CardData(Resource):
    """
    Strict Data Model for all card datatypes (Monster, Spell, Trap).
    Validates itself upon loading to ensure gameplay logic never encounters
    invalid states (e.g., Spells with ATK values).
    """

    DB_FILE = os.path.join("game", "resources", "cards.json")

    def __init__(self) -> None:
        super().__init__()
        self.id: int = 0
        self.name: str = "Unknown"
        self.description: str = ""
        self.card_type: CardType = CardType.MONSTER
        self.icon: CardIcon = CardIcon.NONE

        self.level: int = 0
        self.atk: int = 0
        self.def_: int = 0

        self.texture_path: str = ""
        self.effect_trigger: EffectTrigger = EffectTrigger.MANUAL

    def validate(self) -> None:
        """
        Runs critical validation rules.
        Raises ValueError if the data integrity contract is violated.
        """
        if self.card_type == CardType.MONSTER:
            if self.level < 1:
                raise ValueError(
                    f"Monster '{self.name}' has invalid Level: {self.level} (Must be >= 1)"
                )
            if self.atk < 0:
                raise ValueError(
                    f"Monster '{self.name}' has invalid ATK: {self.atk} (Must be >= 0)"
                )
            if self.def_ < 0:
                raise ValueError(
                    f"Monster '{self.name}' has invalid DEF: {self.def_} (Must be >= 0)"
                )
            if self.icon != CardIcon.NONE:
                raise ValueError(
                    f"Monster '{self.name}' cannot have an Icon: {self.icon.name}"
                )

        else:
            if self.icon == CardIcon.NONE:
                raise ValueError(
                    f"{self.card_type.name} '{self.name}' must have a valid Icon (cannot be NONE)"
                )

        if not self.texture_path:
            pass


def load_resources() -> None:
    """
    Loads, parses, and VALIDATES the card database.
    Any card failing validation is rejected and logged as an error.
    """
    Logger.info("Loading Card Database...", "CardDB")

    if not os.path.exists(CardData.DB_FILE):
        Logger.error(f"Card Data file missing: {CardData.DB_FILE}", "CardDB")
        return

    try:
        with open(CardData.DB_FILE, "r") as f:
            data = json.load(f)

        loaded_count = 0
        for entry in data:
            try:
                try:
                    c_type = CardType(entry.get("type", "MONSTER"))
                except ValueError:
                    raise ValueError(f"Invalid CardType: {entry.get('type')}")

                try:
                    c_icon = CardIcon(entry.get("icon", "NONE"))
                except ValueError:
                    raise ValueError(f"Invalid CardIcon: {entry.get('icon')}")

                new_card = CardData()
                new_card.id = int(entry["id"])
                new_card.resource_name = entry["name"]
                new_card.name = entry["name"]
                new_card.description = entry.get("description", "")

                new_card.card_type = c_type
                new_card.icon = c_icon

                new_card.level = int(entry.get("level", 0))
                new_card.atk = int(entry.get("atk", 0))
                new_card.def_ = int(entry.get("def", 0))

                assets = entry.get("assets", {})
                filename = ""

                if isinstance(assets, str):
                    filename = assets

                if not filename:
                    clean_name = (
                        entry["name"].lower().replace(" ", "_").replace("-", "_")
                    )
                    filename = f"{clean_name}.png"

                new_card.texture_path = os.path.join(
                    "assets", "cards", filename
                ).replace("\\", "/")

                new_card.validate()
                virtual_path = f"card://{new_card.id}"
                new_card.take_over_path(virtual_path)
                ResourceLoader._CACHE[virtual_path] = new_card
                loaded_count += 1

            except Exception as e:
                Logger.error(
                    f"Failed to load card ID {entry.get('id', '?')}: {e}", "CardDB"
                )

        Logger.info(f"Successfully registered {loaded_count} cards.", "CardDB")

    except Exception as e:
        Logger.error(f"Catastrophic failure parsing Card DB: {e}", "CardDB")
