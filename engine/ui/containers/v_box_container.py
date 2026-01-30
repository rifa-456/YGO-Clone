from engine.ui.containers.box_container import BoxContainer


class VBoxContainer(BoxContainer):
    def __init__(self, separation: int = 4, name="VBox"):
        super().__init__(vertical=True, separation=separation, name=name)
