import json
import os
from typing import List
from engine.logger import Logger
from engine.core.resource_loader import ResourceLoader
from game.autoload.card_database import CardData


class DeckRepository:
    """
    Handles saving/loading Player Decks (JSON) and converting them
    into usable CardData Resources.
    """

    @staticmethod
    def load_deck(path: str) -> List[CardData]:
        """
        Reads a JSON deck file and returns a list of CardData objects.
        """
        if not os.path.exists(path):
            Logger.error(f"Deck file not found: {path}", "DeckRepo")
            return []

        try:
            with open(path, "r") as f:
                data = json.load(f)

            card_ids = data.get("cards", [])
            resources: List[CardData] = []
            for c_id in card_ids:
                v_path = f"card://{c_id}"
                card_res = ResourceLoader.load(v_path, CardData)
                if card_res:
                    resources.append(card_res)
                else:
                    Logger.error(f"Deck contains unknown card: {c_id}", "DeckRepo")

            Logger.info(
                f"Loaded deck '{data.get('name')}' with {len(resources)} cards.",
                "DeckRepo",
            )
            return resources

        except Exception as e:
            Logger.error(f"Failed to load deck: {e}", "DeckRepo")
            return []

    @staticmethod
    def save_deck(path: str, name: str, cards: List[CardData]) -> None:
        """
        Serializes a list of CardData objects back to a JSON file.
        """
        try:
            data = {"name": name, "cards": [card.id for card in cards]}
            with open(path, "w") as f:
                json.dump(data, f, indent=4)

            Logger.info(f"Saved deck to {path}", "DeckRepo")

        except Exception as e:
            Logger.error(f"Failed to save deck: {e}", "DeckRepo")
