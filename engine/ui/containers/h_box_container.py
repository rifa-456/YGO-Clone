from engine.ui.containers.box_container import BoxContainer


class HBoxContainer(BoxContainer):
    def __init__(self, separation: int = 4, name="HBox"):
        super().__init__(vertical=False, separation=separation, name=name)
