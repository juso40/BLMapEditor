from typing import cast

from imgui_bundle import imgui

from ... import selectedobject as sobj
from ...placeables.prefab import Prefab


def draw() -> None:
    _draw_children()
    imgui.spacing()
    imgui.separator()
    imgui.spacing()
    imgui.spacing()
    imgui.spacing()
    imgui.spacing()


def _draw_children() -> None:
    game_obj: Prefab = cast(Prefab, sobj.SELECTED_OBJECT)
    imgui.begin_child("Prefab Parts", size=(0, 0), child_flags=imgui.ChildFlags_.borders.value)
    for part in game_obj.component_data:
        imgui.bullet_text(f"{part.data.name} ({part.data.rename})")
    imgui.end_child()
