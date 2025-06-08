from __future__ import annotations

import pathlib
from collections.abc import Callable
from typing import TYPE_CHECKING, cast

from imgui_bundle import imgui
from mods_base import get_pc

from .. import prefabbuffer as pb
from .. import selectedobject as sobj
from . import saveprefabmodal

if TYPE_CHECKING:
    from common import WillowPlayerController

Callback = Callable[[], None]

CALLBACK_COPY: Callback = lambda: sobj.HELPER_INSTANCE.copy() if sobj.HELPER_INSTANCE else None
CALLBACK_PASTE: Callback = lambda: sobj.HELPER_INSTANCE.paste() if sobj.HELPER_INSTANCE else None
CALLBACK_DELETE: Callback = lambda: sobj.HELPER_INSTANCE.delete_object() if sobj.HELPER_INSTANCE else None
CALLBACK_TOGGLE_PREFAB: Callback = lambda: sobj.HELPER_INSTANCE.add_to_prefab() if sobj.HELPER_INSTANCE else None
CALLBACK_SAVE_PREFAB: Callback = saveprefabmodal.draw_save_prefab_modal
CALLBACK_CANCEL_PREFAB: Callback = lambda: pb.prefab_buffer.clear()
CALLBACK_TP_TO_OBJECT: Callback = lambda: (
    None  # noqa: RUF034
    if sobj.HELPER_INSTANCE and sobj.HELPER_INSTANCE.tp_to_selected_object(cast("WillowPlayerController", get_pc()))
    else None
)

_INPUT_TEXT_SAVE_MODAL: str = "Prefab Name"
_PREFABS_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent / "Prefabs"
_PREFABS_PATH.mkdir(exist_ok=True)


def draw_toolbar() -> None:  # noqa: PLR0912
    # Place it directly under the menu bar
    imgui.set_next_window_pos((0, imgui.get_frame_height()))
    imgui.set_next_window_size((imgui.get_io().display_size[0], imgui.get_frame_height()))
    imgui.begin(
        "Toolbar",
        flags=imgui.WindowFlags_.no_title_bar.value
        | imgui.WindowFlags_.no_resize.value
        | imgui.WindowFlags_.no_move.value
        | imgui.WindowFlags_.no_saved_settings.value
        | imgui.WindowFlags_.no_scrollbar.value
        | imgui.WindowFlags_.no_collapse.value
        | imgui.WindowFlags_.no_focus_on_appearing.value
        | imgui.WindowFlags_.no_docking.value,
    )
    if imgui.button("Copy"):
        CALLBACK_COPY()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Copy selected objects to clipboard")
    imgui.same_line()

    if imgui.button("Paste"):
        CALLBACK_PASTE()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Paste objects from clipboard")
    imgui.same_line()

    if imgui.button("Delete"):
        CALLBACK_DELETE()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Delete selected objects")
    imgui.same_line()

    if imgui.button("Toggle Prefab"):
        CALLBACK_TOGGLE_PREFAB()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Add/Remove current object to/from a prefab.")
    imgui.same_line()

    if imgui.button("Save Prefab"):
        CALLBACK_SAVE_PREFAB()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Save selected objects as a prefab.")
    saveprefabmodal.try_show_save_prefab_modal()
    imgui.same_line()

    if imgui.button("Clear Prefab"):
        CALLBACK_CANCEL_PREFAB()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Clear the current prefab buffer.")
    imgui.same_line()

    if imgui.button("TP To Object"):
        CALLBACK_TP_TO_OBJECT()
    elif imgui.is_item_hovered():
        imgui.set_tooltip("Teleport to the selected object.")

    imgui.end()
