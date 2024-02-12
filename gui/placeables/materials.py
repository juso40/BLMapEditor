from typing import List

import imgui
import unrealsdk  # type: ignore

from ... import bl2tools
from ... import selectedobject as sobj
from ... import placeables

_material_instances: List[unrealsdk.UObject] = []
_material_instances_filtered: List[unrealsdk.UObject] = []
_material_instances_filtered_names: List[str] = []
_selected_material_index: int = -1
_selected_material_index_modal: int = -1

material_filter: str = ""
SHOW_MATERIAL_MODAL: bool = False


def draw() -> None:
    global SHOW_MATERIAL_MODAL, _selected_material_index  # noqa: PLW0603

    assert sobj.SELECTED_OBJECT is not None
    game_obj: placeables.AbstractPlaceable = sobj.SELECTED_OBJECT
    imgui.push_item_width(-1)
    if imgui.button("Add Material"):
        SHOW_MATERIAL_MODAL = True
        _material_instances.extend(unrealsdk.FindAll("MaterialInstanceConstant")[1:])

    if SHOW_MATERIAL_MODAL:
        imgui.open_popup("Add Material")
    if imgui.begin_popup_modal(title="Add Material", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
        _material_modal()

    imgui.same_line()
    if imgui.button("Remove Material"):
        game_obj.remove_material(index=_selected_material_index)
    imgui.text("Materials")
    _selected_material_index = imgui.listbox(
        "##Materials",
        _selected_material_index,
        [bl2tools.get_obj_path_name(x) for x in game_obj.get_materials()],
    )[1]
    imgui.spacing()
    imgui.separator()
    imgui.spacing()
    imgui.spacing()
    imgui.pop_item_width()


def _material_modal() -> None:
    global SHOW_MATERIAL_MODAL, material_filter  # noqa: PLW0603
    global _material_instances_filtered, _material_instances_filtered_names, _selected_material_index_modal  # noqa: PLW0603
    imgui.push_item_width(500)

    assert sobj.SELECTED_OBJECT is not None
    game_obj: placeables.AbstractPlaceable = sobj.SELECTED_OBJECT
    imgui.text("Filter Materials")
    b_filtered, material_filter = imgui.input_text("##Filter Materials", material_filter, 24)
    if b_filtered:
        _material_instances_filtered = [
            x for x in _material_instances if material_filter.lower() in bl2tools.get_obj_path_name(x).lower()
        ]
        _material_instances_filtered_names = [bl2tools.get_obj_path_name(x) for x in _material_instances_filtered]

    _selected_material_index_modal = imgui.listbox(
        "##Materials",
        _selected_material_index_modal,
        _material_instances_filtered_names,
        24,
    )[1]

    if imgui.button("Add Material"):
        game_obj.add_material(_material_instances_filtered[_selected_material_index_modal])
    if imgui.button("Remove Material"):
        game_obj.remove_material(material=_material_instances_filtered[_selected_material_index_modal])
    if imgui.button("Close"):
        SHOW_MATERIAL_MODAL = False
        _material_instances.clear()
        _material_instances_filtered.clear()
        _material_instances_filtered_names.clear()
        material_filter = ""
        _selected_material_index_modal = -1
        imgui.close_current_popup()
    imgui.pop_item_width()
    imgui.end_popup()
