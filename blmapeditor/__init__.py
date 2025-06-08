from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, cast

import blimgui
from mods_base import ENGINE, build_mod, keybinds
from unrealsdk import hooks, unreal

from . import editor, settings

if TYPE_CHECKING:
    from common import WillowGameEngine

    ENGINE = cast(WillowGameEngine, ENGINE)

IMGUI_SHOW: bool = False


class State:
    Editor: editor.Editor = editor.instance
    pass_input: bool = False


def _toggle() -> None:
    global IMGUI_SHOW  # noqa: PLW0603
    if IMGUI_SHOW:
        blimgui.close_window()
        IMGUI_SHOW = False
    else:
        blimgui.set_draw_callback(State.Editor.render)
        blimgui.create_window("Map Editor")
        IMGUI_SHOW = True


def on_enable() -> None:
    State.pass_input = True

    def end_load(_obj: unreal.UObject, _args: unreal.WrappedStruct, _ret: Any, _func: unreal.BoundFunction) -> None:
        level_name: str = ENGINE.GetCurrentWorldInfo().GetStreamingPersistentMapName().lower()
        State.Editor.end_loading(level_name)

    def start_load(_obj: unreal.UObject, args: unreal.WrappedStruct, _ret: Any, _func: unreal.BoundFunction) -> None:
        if args.MovieName is None:
            return
        State.Editor.start_loading(args.MovieName.lower())

    hooks.add_hook(
        "WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie",
        hooks.Type.PRE,
        __file__,
        end_load,
    )
    hooks.add_hook(
        "WillowGame.WillowPlayerController:WillowClientShowLoadingMovie",
        hooks.Type.PRE,
        __file__,
        start_load,
    )


def on_disable() -> None:
    State.pass_input = False

    hooks.remove_hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", hooks.Type.PRE, __file__)
    hooks.remove_hook("WillowGame.WillowPlayerController:WillowClientShowLoadingMovie", hooks.Type.PRE, __file__)



mod = build_mod(
    options=settings.ALL_OPTIONS,
    keybinds=[
        keybinds.KeybindType("Restore Object Defaults", "Backspace", callback=State.Editor.restore_objects_default),
        keybinds.KeybindType("Toggle Editor", "F1", callback=State.Editor.toggle_enable),
        keybinds.KeybindType("TP To Object", "F2", callback=State.Editor.tp_to_selected_object),
        keybinds.KeybindType("Lock Obj in Place", "F3", callback=State.Editor.toggle_lock_object_position),
        keybinds.KeybindType("Delete Obj", "Delete", callback=State.Editor.delete_selected_object),
        keybinds.KeybindType("TP my Pawn to me", "F5", callback=State.Editor.tp_pawn_to_camera),
        keybinds.KeybindType("Toggle Preview", "P", callback=State.Editor.toggle_preview),
        keybinds.KeybindType("Toggle Editor Window", "Home", callback=_toggle),
        keybinds.KeybindType(
            "Cycle Editing Mode",
            "Tab",
            is_rebindable=False,
            callback=State.Editor.cycle_editing_mode,
        ),
        keybinds.KeybindType(
            "Axis X",
            "X",
            is_rebindable=False,
            callback=partial(State.Editor.update_edit_axis, "Axis X"),
        ),
        keybinds.KeybindType(
            "Axis Y",
            "Y",
            is_rebindable=False,
            callback=partial(State.Editor.update_edit_axis, "Axis Y"),
        ),
        keybinds.KeybindType(
            "Axis Z",
            "Z",
            is_rebindable=False,
            callback=partial(State.Editor.update_edit_axis, "Axis Z"),
        ),
    ],
    on_enable=on_enable,
    on_disable=on_disable,
)
