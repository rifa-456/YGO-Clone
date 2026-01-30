from engine.ui.containers.base_container import Container
from engine.ui.control import Control
from engine.ui.enums import SizeFlag
from engine.math.datatypes.vector2 import Vector2
from engine.math.datatypes.rect2 import Rect2


class BoxContainer(Container):
    def __init__(self, vertical: bool, separation: int = 0, name: str = "BoxContainer"):
        super().__init__(name)
        self.vertical = vertical
        self.separation = separation

    def _calculate_min_size(self):
        total_primary = 0.0
        max_secondary = 0.0
        visible_children_count = 0

        for child in self.children:
            if isinstance(child, Control) and child.visible:
                visible_children_count += 1
                ms = child.get_combined_minimum_size()
                if self.vertical:
                    total_primary += ms.y
                    max_secondary = max(max_secondary, ms.x)
                else:
                    total_primary += ms.x
                    max_secondary = max(max_secondary, ms.y)

        if visible_children_count > 1:
            total_primary += self.separation * (visible_children_count - 1)

        if self.vertical:
            self._cached_min_size = Vector2(max_secondary, total_primary)
        else:
            self._cached_min_size = Vector2(total_primary, max_secondary)

    def _reflow_children(self):
        controls = [c for c in self.children if isinstance(c, Control) and c.visible]
        if not controls:
            return

        my_rect = self.get_rect()
        total_primary_size = my_rect.size.y if self.vertical else my_rect.size.x
        total_secondary_size = my_rect.size.x if self.vertical else my_rect.size.y

        total_min_primary = 0.0
        total_stretch_ratio = 0.0
        expanding_count = 0

        separation_space = float(self.separation * (len(controls) - 1)) if len(controls) > 1 else 0.0
        total_min_primary += separation_space

        for c in controls:
            ms = c.get_combined_minimum_size()
            c_min_p = ms.y if self.vertical else ms.x
            total_min_primary += c_min_p

            flag = c.size_flags_vertical if self.vertical else c.size_flags_horizontal
            if flag & SizeFlag.EXPAND:
                expanding_count += 1
                total_stretch_ratio += c.size_flags_stretch_ratio

        remaining_space = max(0.0, total_primary_size - total_min_primary)

        offset = 0.0

        for i, c in enumerate(controls):
            ms = c.get_combined_minimum_size()
            current_prim = ms.y if self.vertical else ms.x
            current_sec = ms.x if self.vertical else ms.y

            flag_prim = c.size_flags_vertical if self.vertical else c.size_flags_horizontal
            flag_sec = c.size_flags_horizontal if self.vertical else c.size_flags_vertical

            if (flag_prim & SizeFlag.EXPAND) and total_stretch_ratio > 0:
                share = (c.size_flags_stretch_ratio / total_stretch_ratio) * remaining_space
                current_prim += share

            final_sec_size = total_secondary_size
            sec_offset = 0.0

            if not (flag_sec & SizeFlag.FILL):
                final_sec_size = current_sec
                if flag_sec & SizeFlag.SHRINK_CENTER:
                    sec_offset = (total_secondary_size - current_sec) * 0.5
                elif flag_sec & SizeFlag.SHRINK_END:
                    sec_offset = total_secondary_size - current_sec

            if self.vertical:
                rect = Rect2(sec_offset, offset, final_sec_size, current_prim)
            else:
                rect = Rect2(offset, sec_offset, current_prim, final_sec_size)

            self.fit_child_in_rect(c, rect)
            offset += current_prim + self.separation

            prev_c = controls[i - 1] if i > 0 else None
            next_c = controls[i + 1] if i < len(controls) - 1 else None

            if self.vertical:
                if prev_c: c.focus_neighbor_top = c.get_path_to(prev_c)
                if next_c: c.focus_neighbor_bottom = c.get_path_to(next_c)
            else:
                if prev_c: c.focus_neighbor_left = c.get_path_to(prev_c)
                if next_c: c.focus_neighbor_right = c.get_path_to(next_c)