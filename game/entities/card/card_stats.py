from game.autoload.card_database import CardData


class CardStats:
    def __init__(self, data: CardData):
        self.data: CardData = data
        self.current_atk: int = data.atk
        self.current_def: int = data.def_
        self.original_atk: int = data.atk
        self.original_def: int = data.def_

    def reset(self):
        """Resets current stats to original values."""
        self.current_atk = self.original_atk
        self.current_def = self.original_def
