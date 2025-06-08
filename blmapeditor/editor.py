from __future__ import annotations

import json
import os
from enum import Flag, IntEnum, auto
from types import ModuleType
from typing import TYPE_CHECKING, cast

from coroutines import PostRenderCoroutine, start_coroutine_post_render
from imgui_bundle import imgui
from mods_base import ENGINE, get_pc
from uemath.constants import URU_1
from unrealsdk import logging

from . import gui, inputmanager, placeablehelpers, settings
from . import selectedobject as sobj

__all__: list[str] = ["instance"]

if TYPE_CHECKING:
    from common import WillowGameEngine, WillowPlayerController, WillowPlayerPawn

ENGINE = cast("WillowGameEngine", ENGINE)


class EEditingMode(IntEnum):
    Place = 0
    Move = auto()
    Scale = auto()
    Rotate = auto()


class EAxis(Flag):
    None_ = 0
    X = auto()
    Y = auto()
    Z = auto()


PLACEABLE_OBJECT_ATTRIBUTES: dict[str, list[ModuleType]] = {
    "StaticMeshComponent": [gui.placeables.metadata, gui.placeables.transform, gui.placeables.materials],
    "AIPawnBalanceDefinition": [gui.placeables.metadata, gui.placeables.transform, gui.placeables.materials],
    "InteractiveObjectDefinition": [gui.placeables.metadata, gui.placeables.transform, gui.placeables.materials],
    "Prefab": [gui.placeables.metadata, gui.placeables.transform, gui.placeables.prefab_parts],
}

PLACEABLE_TO_HELPER: dict[str, placeablehelpers.PlaceableHelper] = {
    "AIPawnBalanceDefinition": placeablehelpers.PawnHelper,
    "InteractiveObjectDefinition": placeablehelpers.InteractiveHelper,
    "Prefab": placeablehelpers.PrefabHelper,
    "StaticMeshComponent": placeablehelpers.SMCHelper,
}


class Editor:
    def __init__(self) -> None:
        self.pc: WillowPlayerController | None = (
            None  # The Current PlayerController instance, cached for performance reasons
        )
        self.pawn: WillowPlayerPawn | None = None  # PlayerPawn instance has to be cached to return to play mode

        self.is_in_editor: bool = False  # Most code will only run while editor mode is active

        self.editor_mode: EEditingMode = EEditingMode.Place  # The current editing mode
        self.editor_mode_text: str = " | ".join(
            [f"[{e.name}]" if e.value == self.editor_mode else e.name for e in EEditingMode],
        )  # The text that is displayed in the top left corner

        self.edit_axis: EAxis = EAxis.None_  # The current axis that is being edited
        self.post_render_info_text = (
            f"Editor Mode: {self.editor_mode_text} \n"
            f"Axis: {[e.name for e in EAxis if e.value & self.edit_axis.value]}"
        )  # The text that is displayed in the top left

        # All available Helper Objects, all have the same interface
        self.placeable_helpers: list[placeablehelpers.PlaceableHelper] = [
            placeablehelpers.SMCHelper,
            placeablehelpers.PawnHelper,
            placeablehelpers.InteractiveHelper,
            placeablehelpers.PrefabHelper,
        ]

    def load_map(self, abs_path: str) -> None:
        """
        Load a custom map from a given .json file.
        """
        for helper in self.placeable_helpers:
            helper.on_enable()  # make sure they are all enabled

        curr_map = ENGINE.GetCurrentWorldInfo().GetStreamingPersistentMapName().lower()
        if os.path.isfile(abs_path):
            with open(abs_path) as fp:
                map_dict = json.load(fp)
        else:
            logging.dev_warning(f"Map '{abs_path}' does not exist!")
            return

        load_this = map_dict.get(curr_map, None)
        if not load_this:
            logging.info("No Map data for currently loaded map found!")
            return
        for helper in self.placeable_helpers:
            helper.load_map(load_this)  # start loading map using all available placeable helpers

    def save_map(self, abs_path: str) -> None:
        """
        Save the current map changes to a .json map file.
        """
        curr_map = ENGINE.GetCurrentWorldInfo().GetStreamingPersistentMapName().lower()
        save_this = {}

        try:
            with open(abs_path) as fp:
                save_this = json.load(fp)
        except json.JSONDecodeError:
            logging.error(
                f"[ERROR] '{abs_path}' seems to not be valid .json! The map could not be loaded, the files content remains unchanged.",
            )
        except FileNotFoundError:
            pass

        # let's overwrite the previous data for this map, as it will get added back anyway
        save_this[curr_map] = {}
        for mode in self.placeable_helpers:
            mode.save_map(save_this[curr_map])

        with open(abs_path, "w") as fp:
            json.dump(save_this, fp)

    def toggle_enable(self) -> None:
        if self.is_in_editor:
            self.disable()
        else:
            self.enable()

    def toggle_lock_object_position(self) -> None:
        settings.b_lock_object_position = not settings.b_lock_object_position

    def delete_selected_object(self) -> None:
        if self.is_in_editor and sobj.SELECTED_OBJECT:
            PLACEABLE_TO_HELPER[sobj.SELECTED_OBJECT.uclass].delete_object()
            sobj.SELECTED_OBJECT = None

    def toggle_preview(self) -> None:
        if not self.is_in_editor:
            return
        settings.b_show_preview = not settings.b_show_preview
        sobj.calculate_preview()  # recalculate the preview if it is enabled

    def tp_pawn_to_camera(self) -> None:
        if not self.is_in_editor or not self.pawn or not self.pc:
            return
        self.pawn.Location.X = self.pc.Location.X
        self.pawn.Location.Y = self.pc.Location.Y
        self.pawn.Location.Z = self.pc.Location.Z

    def cycle_editing_mode(self) -> None:
        if not self.is_in_editor:
            return
        self.editor_mode = EEditingMode((self.editor_mode.value + 1) % len(EEditingMode))
        self._update_post_render_info_text()

    def update_edit_axis(self, axis: str, check_exclude_modifier: bool = True) -> None:
        exclude = inputmanager.is_key_pressed("LeftShift") if check_exclude_modifier else False
        if axis == "Axis X":
            if exclude:
                self.edit_axis = EAxis.Y | EAxis.Z
            else:
                self.edit_axis = EAxis.X
        elif axis == "Axis Y":
            if exclude:
                self.edit_axis = EAxis.X | EAxis.Z
            else:
                self.edit_axis = EAxis.Y
        elif axis == "Axis Z":
            if exclude:
                self.edit_axis = EAxis.X | EAxis.Y
            else:
                self.edit_axis = EAxis.Z
        else:
            self.edit_axis = EAxis.None_
        self._update_post_render_info_text()

    def _update_post_render_info_text(self) -> None:
        self.editor_mode_text = " | ".join(
            [f"[{e.name}]" if e.value == self.editor_mode else e.name for e in EEditingMode],
        )
        self.post_render_info_text = (
            f"Editor Mode: {self.editor_mode_text} \n"
            f"Axis: {[e.name for e in EAxis if e.value & self.edit_axis.value]}"
        )  # The text that is displayed in the top left

    def tp_to_selected_object(self) -> None:
        """
        This function gets called for the "TP to Obj" keybind.
        If we are in "Create" or in "Prefabs" filter, don't do anything and tell the user.
        """
        if sobj.SELECTED_OBJECT and self.is_in_editor:
            PLACEABLE_TO_HELPER[sobj.SELECTED_OBJECT.uclass].tp_to_selected_object(
                self.pc or cast("WillowPlayerController", get_pc()),
            )

    def restore_objects_default(self) -> None:
        if self.is_in_editor and sobj.SELECTED_OBJECT:
            PLACEABLE_TO_HELPER[sobj.SELECTED_OBJECT.uclass].restore_objects_defaults()

    def _copy(self) -> None:
        """This function gets called for the "Copy" keybind."""
        if not self.is_in_editor:
            return
        if sobj.SELECTED_OBJECT:
            PLACEABLE_TO_HELPER[sobj.SELECTED_OBJECT.uclass].copy()
        elif sobj.HELPER_INSTANCE:
            sobj.HELPER_INSTANCE.copy()

    def _paste(self) -> None:
        """This function gets called for the "Paste" keybind."""
        if not self.is_in_editor:
            return
        if sobj.CLIPBOARD and sobj.CLIPBOARD_HELPER:
            sobj.CLIPBOARD_HELPER.paste()

    def _left_mouse_button_pressed(self) -> None:
        """This function gets called when the left mouse button is pressed."""
        if not self.is_in_editor:
            return
        if self.editor_mode == EEditingMode.Place:
            copy_buffer = sobj.CLIPBOARD
            self._copy()
            self._paste()
            sobj.CLIPBOARD = copy_buffer

    def _right_mouse_button_pressed(self) -> None:
        """This function gets called when the right mouse button is pressed."""
        if not self.is_in_editor:
            return
        if self.editor_mode == EEditingMode.Place:
            if sobj.SELECTED_OBJECT:  # If we have an object selected
                PLACEABLE_TO_HELPER[sobj.SELECTED_OBJECT.uclass].cancel_editing()  # toggle it off
                gui.placeables.materials.SHOW_MATERIAL_MODAL = False
        else:
            self.update_edit_axis("Axis None", check_exclude_modifier=False)

    def _mouse_scroll_up(self) -> None:
        self._mouse_scroll(1)

    def _mouse_scroll_down(self) -> None:
        self._mouse_scroll(-1)

    def _mouse_scroll(self, direction: int) -> None:
        """
        This function gets called when the mouse wheel is scrolled.
        """
        if not sobj.SELECTED_OBJECT:
            return
        if self.editor_mode == EEditingMode.Move:
            settings.editor_offset += 20 * direction

        elif self.editor_mode == EEditingMode.Scale:
            if self.edit_axis == EAxis.None_:
                sobj.SELECTED_OBJECT.add_scale(0.05 * direction)
            else:
                _x, _y, _z = sobj.SELECTED_OBJECT.get_scale3d()
                sobj.SELECTED_OBJECT.set_scale3d(
                    [
                        _x + direction * 0.05 if self.edit_axis & EAxis.X else _x,
                        _y + direction * 0.05 if self.edit_axis & EAxis.Y else _y,
                        _z + direction * 0.05 if self.edit_axis & EAxis.Z else _z,
                    ],
                )

        elif self.editor_mode == EEditingMode.Rotate:
            sobj.SELECTED_OBJECT.add_rotation(
                (
                    direction * URU_1 if self.edit_axis & EAxis.X else 0,
                    direction * URU_1 if self.edit_axis & EAxis.Y else 0,
                    direction * URU_1 if self.edit_axis & EAxis.Z else 0,
                ),
            )

    def render(self) -> None:
        gui.menubar.draw_menu_bar()
        gui.toolbar.draw_toolbar()
        gui.statusbar.draw_statusbar()
        gui.docking_area.draw_docking_area()
        gui.quicksettings.draw_settings_menu()
        gui.placeablelist.draw_placeables_window(self.pc or get_pc(), self.placeable_helpers)

        imgui.begin("Object Attributes")
        if sobj.SELECTED_OBJECT:
            for attr in PLACEABLE_OBJECT_ATTRIBUTES.get(sobj.SELECTED_OBJECT.uclass, []):
                attr.draw()
        imgui.end()

    def register_input_callbacks(self) -> None:
        inputmanager.register_callback("LeftMouseButton", self._left_mouse_button_pressed)
        inputmanager.register_callback("RightMouseButton", self._right_mouse_button_pressed)
        inputmanager.register_callback("MouseScrollUp", self._mouse_scroll_up)
        inputmanager.register_callback("MouseScrollDown", self._mouse_scroll_down)

    def unregister_input_callbacks(self) -> None:
        inputmanager.unregister_callback("LeftMouseButton", self._left_mouse_button_pressed)
        inputmanager.unregister_callback("RightMouseButton", self._right_mouse_button_pressed)
        inputmanager.unregister_callback("MouseScrollUp", self._mouse_scroll_up)
        inputmanager.unregister_callback("MouseScrollDown", self._mouse_scroll_down)

    def enable(self) -> None:
        self.is_in_editor = True
        self.pc = cast("WillowPlayerController", get_pc())
        # Set up the editing mode
        ENGINE.GetCurrentWorldInfo().bPlayersOnly = True
        self.pawn = self.pc.GetWillowPlayerPawn()
        self.pc.HideHUD()
        self.pc.ServerSpectate()
        self.pc.bCollideWorld = False
        # Attach Callbacks
        gui.quicksettings.callback_checkbox_show_preview = lambda _: sobj.calculate_preview()
        gui.menubar.callback_save_map = self.save_map
        gui.menubar.callback_load_map = self.load_map

        self.register_input_callbacks()
        start_coroutine_post_render(self.on_post_render())

    def on_post_render(self) -> PostRenderCoroutine:
        while True:
            yield None  # No condition needed here, just give me the canvas
            canvas = yield
            canvas = canvas()
            if not canvas:
                continue

            canvas.SetPos(20, 20, 0)
            canvas.SetDrawColorStruct(canvas.MakeColor(R=0, G=255, B=0, A=255))
            canvas.DrawText(self.post_render_info_text, False, 1, 1)
            if not self.pc:
                return None
            sobj.move_tick(self.pc, settings.editor_offset)

            if not self.is_in_editor:
                return None  # Break this coroutine

    def disable(self) -> None:
        sobj.destroy_preview()
        self.is_in_editor = False
        self.pc = cast("WillowPlayerController", get_pc())
        ENGINE.GetCurrentWorldInfo().bPlayersOnly = False
        self.pc.Possess(self.pawn, True)
        self.pc.DisplayHUD()
        self.unregister_input_callbacks()

    def start_loading(self, map_name: str) -> None:
        # when we start to travel it would be good to remove any reference to possibly GC objects
        for helper in self.placeable_helpers:
            helper.cleanup(map_name)

    def end_loading(self, _map_name: str) -> None:
        self.pc = cast("WillowPlayerController", get_pc())
        for helper in self.placeable_helpers:
            helper.b_setup = True


instance = Editor()
