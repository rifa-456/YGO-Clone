from engine.scene.main.signal import Signal


class GameEvents:
    """
    Global Event Bus (Singleton).
    Decouples Game Logic (Rules) from Game Content (Cards).
    """

    _instance = None

    def __init__(self):
        self.on_attack_declared = Signal("on_attack_declared")
        self.on_damage_step = Signal("on_damage_step")

        self.on_summon_attempt = Signal("on_summon_attempt")
        self.on_summon_success = Signal("on_summon_success")

        self.on_phase_change = Signal("on_phase_change")

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = GameEvents()
        return cls._instance
