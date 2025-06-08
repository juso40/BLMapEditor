from typing import cast

from imgui_bundle import imgui
from mods_base import options
from unrealsdk import unreal  # type: ignore

from .. import selectedobject as sobj
from .. import settings
from ..placeablehelpers import PlaceableHelper

NAME_TO_OPTION: dict[str, options.HiddenOption] = {o.identifier: o for o in settings.ALL_OPTIONS}
del NAME_TO_OPTION[settings.show_quicksettings_window.identifier]


def draw_placeables_window(pc: unreal.UObject, placeable_helpers: list[PlaceableHelper]) -> None:
    _navigate_with_keyboard()
    for ph in placeable_helpers:
        _option = NAME_TO_OPTION[ph.name]
        if _option.value:
            _, _option.value = imgui.begin(ph.name, p_open=True)
            if imgui.is_window_focused():
                sobj.HELPER_INSTANCE = ph
            ph.on_enable()
            _populate_window(pc, ph)
            imgui.end()


def _navigate_with_keyboard() -> None:
    if sobj.HELPER_INSTANCE is None or not imgui.is_window_focused():
        return

    ph: PlaceableHelper = cast(PlaceableHelper, sobj.HELPER_INSTANCE)
    objs = ph.get_names_for_filter()  # get the filtered cached objects
    if not objs:  # No objects, just return
        return
    max_index = len(objs) - 1  # calculate the max index
    if imgui.is_key_pressed(imgui.Key.up_arrow):  # Scroll Up, index -= 1
        if max_index == 0:  # if there are no objects, set the index to -1
            ph.object_index = 0
        else:
            ph.object_index = (ph.object_index - 1) % (max_index + 1)
        ph.update_preview()
    if imgui.is_key_pressed(imgui.Key.down_arrow):  # Scroll Down, index += 1
        if max_index == 0:
            ph.object_index = 0
        else:
            ph.object_index = (ph.object_index + 1) % (max_index + 1)
        ph.update_preview()


def _populate_window(_pc: unreal.UObject, ph: PlaceableHelper) -> None:
    if imgui.button("Refresh"):
        ph.is_cache_dirty = True
    if imgui.is_item_hovered():
        imgui.set_tooltip("Refresh the list of objects. Useful if you renamed an object.")

    changed, current = imgui.combo("Filters", ph.available_filters.index(ph.curr_filter), ph.available_filters)
    if changed:
        ph.search_string = ""
        ph.object_index = -1
        ph.is_cache_dirty = True
        ph.curr_filter = ph.available_filters[current]

    in_text = imgui.input_text("Search", ph.search_string, 20)
    if in_text[0]:
        ph.search_string = in_text[1]
        ph.is_cache_dirty = True

    if sobj.SELECTED_OBJECT is None:
        if imgui.button("Edit/Create Selected Object"):
            ph.move_object()
    elif imgui.button("Done/ Deselect"):
        ph.move_object()
    imgui.spacing()
    imgui.begin_child(
        "##placeablelist",
        size=(0, 0),
        # window_flags=imgui.WindowFlags_.horizontal_scrollbar.value | imgui.WindowFlags_.always_auto_resize.value,
    )
    imgui.push_item_width(-1)
    list_selected = imgui.list_box(
        f"##{ph.curr_filter}",
        ph.object_index,
        ph.get_names_for_filter(),
        int((imgui.get_content_region_avail()[1] // imgui.get_frame_height()) * 1.25) - 1,
    )
    if list_selected[0]:
        ph.object_index = list_selected[1]
        ph.update_preview()

    imgui.text(f"{ph.object_index + 1}/{len(ph.get_names_for_filter())}")
    imgui.pop_item_width()
    imgui.end_child()
