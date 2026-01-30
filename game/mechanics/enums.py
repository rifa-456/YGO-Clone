from enum import Enum, auto


class EffectTrigger(Enum):
    MANUAL = "MANUAL"
    ON_ATTACK = "ON_ATTACK"
    ON_SUMMON = "ON_SUMMON"


class TargetScope(Enum):
    SELF = "SELF"
    OPPONENT_FIELD = "OPPONENT_FIELD"
    ALL_FIELD = "ALL_FIELD"
    TRIGGER_SOURCE = "TRIGGER_SOURCE"


class GameGroups:
    """
    Standardized Group IDs for the Scene Tree (DuelRules emulation).
    """

    PLAYER_MONSTERS = "player_monsters"
    ENEMY_MONSTERS = "enemy_monsters"
    PLAYER_SPELLS = "player_spells"
    ENEMY_SPELLS = "enemy_spells"
