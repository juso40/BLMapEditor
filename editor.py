import json
import os
from typing import List, cast
from enum import IntEnum, Flag, auto

import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import placeablehelper
from . import settings
from . import canvasutils
from ..ModMenu import Keybind

import imgui

__all__ = ["instance"]


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


class Editor:
    def __init__(self):
        self.pc: unrealsdk.UObject = None  # The Current PlayerController instance, cached for performance reasons
        self.pawn: unrealsdk.UObject = None  # PlayerPawn instance has to be cached to return to play mode

        self.path: os.PathLike = os.path.dirname(os.path.realpath(__file__))

        self.is_in_editor: bool = False  # Most code will only run while editor mode is active

        self.editor_mode: EEditingMode = EEditingMode.Place  # The current editing mode
        self.editor_mode_text: str = " | ".join(
            [f"[{e.name}]" if e.value == self.editor_mode else e.name for e in EEditingMode]
        )  # The text that is displayed in the top left corner

        self.edit_axis: EAxis = EAxis.None_  # The current axis that is being edited
        self.post_render_info_text = (
            f"Editor Mode: {self.editor_mode_text} \n"
            f"Axis: {[e.name for e in EAxis if e.value & self.edit_axis.value]}"
        )  # The text that is displayed in the top left

        # All available Helper Objects, all have the same interface
        self.placeable_helpers: List[placeablehelper.PlaceableHelper] = [placeablehelper.SMCHelper,
                                                                         placeablehelper.PawnHelper,
                                                                         placeablehelper.InteractiveHelper]
        # The currently selected Placeable Helper Mode
        self.curr_phelper: placeablehelper.PlaceableHelper = cast(
            placeablehelper.PlaceableHelper,
            self.placeable_helpers[0]
        )

        self.editor_offset: int = 200  # distance between object origin and player

        self.load_save_map_name: str = ""

    def load_map(self, name: str) -> None:
        """
        Load a custom map from a given .json file.

        :param name: The name of the .json map file.
        :return:
        """
        for helper in self.placeable_helpers:
            helper.on_enable()  # make sure they are all enabled

        curr_map = bl2tools.get_world_info().GetStreamingPersistentMapName().lower()  # get the current map
        if os.path.isfile(os.path.join(self.path, "Maps", f"{name}.json")):
            with open(os.path.join(self.path, "Maps", f"{name}.json")) as fp:
                map_dict = json.load(fp)
        else:
            unrealsdk.Log(f"Map {os.path.join(self.path, 'Maps', f'{name}.json')} does not exist!")
            return

        load_this = map_dict.get(curr_map, None)
        if not load_this:
            unrealsdk.Log("No Map data for currently loaded map found!")
            return
        for helper in self.placeable_helpers:
            helper.load_map(load_this)  # start loading map using all available placeable helpers

    def save_map(self, name: str) -> None:
        """
        Save the current map changes to a .json map file.

        :param name: The name for the .json map file.
        :return:
        """
        curr_map = bl2tools.get_world_info().GetStreamingPersistentMapName().lower()
        save_this = {}

        try:
            with open(os.path.join(self.path, "Maps", f"{name}.json")) as fp:
                save_this = json.load(fp)
        except json.JSONDecodeError:
            unrealsdk.Log(
                f"[ERROR] {name}.json seems to not be valid .json! The map could not be loaded, the files content "
                f"remains unchanged."
            )
        except FileNotFoundError:
            pass

        # let's overwrite the previous data for this map, as it will get added back anyways
        save_this[curr_map] = {}
        for mode in self.placeable_helpers:
            mode.save_map(save_this[curr_map])

        if not os.path.isdir(os.path.join(self.path, "Maps")):
            os.makedirs(os.path.join(self.path, "Maps"))
        with open(os.path.join(self.path, "Maps", f"{name}.json"), "w") as fp:
            json.dump(save_this, fp)

    def game_input_pressed(self, key: Keybind) -> None:
        self.pc = bl2tools.get_player_controller()  # let's rather get the pc each input than each rendered frame
        player_input = self.pc.PlayerInput
        shift_pressed: bool = any("Shift" in pressed_key for pressed_key in player_input.PressedKeys)

        if key.Name == "Toggle Editor":
            if self.is_in_editor:
                self.disable()
            else:
                self.enable()
        elif not self.is_in_editor:
            return

        elif key.Name == "Lock Obj in Place":
            settings.b_lock_object_position = not settings.b_lock_object_position
        elif key.Name == "Delete Obj":
            self.curr_phelper.delete_object()
        elif key.Name == "Toggle Preview":
            settings.b_show_preview = not settings.b_show_preview
            self.curr_phelper.calculate_preview()
        elif key.Name == "TP To Object":
            self._tp_to_selected_object()
        elif key.Name == "TP my Pawn to me":
            self.pawn.Location = (self.pc.Location.X, self.pc.Location.Y, self.pc.Location.Z)
        elif key.Name == "Restore Object Defaults":
            self._restore_objects_default()
        elif key.Name == "Cycle Editing Mode":
            self.editor_mode = EEditingMode((self.editor_mode.value + 1) % len(EEditingMode))
            self._update_post_render_info_text()
        if key.Name.startswith("Axis"):
            self._update_edit_axis(key.Name, shift_pressed)

    def _update_edit_axis(self, axis: str, exclude: bool) -> None:
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
        self._update_post_render_info_text()

    def _update_post_render_info_text(self) -> None:
        self.editor_mode_text = " | ".join(
            [f"[{e.name}]" if e.value == self.editor_mode else e.name for e in EEditingMode]
        )
        self.post_render_info_text = (
            f"Editor Mode: {self.editor_mode_text} \n"
            f"Axis: {[e.name for e in EAxis if e.value & self.edit_axis.value]}"
        )  # The text that is displayed in the top left

    def _tp_to_selected_object(self) -> None:
        """
        This function gets called for the "TP to Obj" keybind.
        If we are in "Create" or in "Prefabs" filter, don't do anything and tell the user.

        :return:
        """
        self.curr_phelper.tp_to_selected_object(self.pc)

    def _restore_objects_default(self) -> None:
        """
        docstring...

        :return:
        """
        self.curr_phelper.restore_objects_defaults()

    def _copy(self) -> None:
        """
        Add the current object to the "clipboard".

        :return:
        """
        self.curr_phelper.copy()

    def _paste(self) -> None:
        """
        Place the object from your current "clipboard" with the same attributes

        :return:
        """
        self.curr_phelper.paste()

    def _left_mouse_button_pressed(self) -> None:
        """
        This function gets called when the left mouse button is pressed.

        :return:
        """
        if self.editor_mode == EEditingMode.Place:
            copy_buffer = self.curr_phelper.clipboard
            self._copy()
            self._paste()
            self.curr_phelper.clipboard = copy_buffer

    def _right_mouse_button_pressed(self) -> None:
        """
        This function gets called when the right mouse button is pressed.

        :return:
        """
        if self.editor_mode == EEditingMode.Place:
            if self.curr_phelper.curr_obj:  # If we have an object selected
                self.curr_phelper.stop_move()  # toggle it off
        else:
            self.edit_axis = EAxis.None_

    def _mouse_scroll(self, direction: int) -> None:
        """
        This function gets called when the mouse wheel is scrolled.

        :param direction: The direction the mouse wheel was scrolled.
        :return:
        """
        if not self.curr_phelper.curr_obj:
            return
        if self.editor_mode == EEditingMode.Move:
            self.editor_offset += 20 * direction

        elif self.editor_mode == EEditingMode.Scale:
            if self.curr_phelper.curr_filter not in ("Prefab BP", "Prefab Instances"):
                if self.edit_axis == EAxis.None_:
                    self.curr_phelper.curr_obj.add_scale(0.05 * direction)
                else:
                    _x, _y, _z = self.curr_phelper.curr_obj.get_scale3d()
                    self.curr_phelper.curr_obj.set_scale3d(
                        [
                            _x + direction * 0.05 if self.edit_axis & EAxis.X else _x,
                            _y + direction * 0.05 if self.edit_axis & EAxis.Y else _y,
                            _z + direction * 0.05 if self.edit_axis & EAxis.Z else _z,
                        ]
                    )

        elif self.editor_mode == EEditingMode.Rotate:
            self.curr_phelper.curr_obj.add_rotation(
                (
                    direction * canvasutils.u_rotation_180 // 180 if self.edit_axis & EAxis.X else 0,
                    direction * canvasutils.u_rotation_180 // 180 if self.edit_axis & EAxis.Y else 0,
                    direction * canvasutils.u_rotation_180 // 180 if self.edit_axis & EAxis.Z else 0
                )
            )

    def draw_settings_menu(self) -> None:
        """
        Draw the Settings UI Window. Populated with various Editor Specific values.
        Most settings will be saved using the SDK SaveModSettings() function.

        :return:
        """
        imgui.begin("Settings")

        settings.b_lock_object_position = imgui.checkbox("Lock Object Position", settings.b_lock_object_position)[1]
        imgui.same_line()
        preview_checked = imgui.checkbox("Show Preview", settings.b_show_preview)
        if preview_checked[0]:
            settings.b_show_preview = preview_checked[1]
            self.curr_phelper.calculate_preview()

        self.pc.SpectatorCameraSpeed = imgui.slider_float("Camera-Speed", self.pc.SpectatorCameraSpeed, 0, 20000)[1]
        self.editor_offset = imgui.slider_float("Camera-Object Distance", self.editor_offset, 0, 2000)[1]
        settings.editor_grid_size = imgui.slider_float("Grid Size", settings.editor_grid_size, 0, 500)[1]

        b_col = imgui.color_edit3(
            "Debug Box Color", *[x / 255 for x in settings.draw_debug_box_color],
            imgui.COLOR_EDIT_PICKER_HUE_BAR
        )

        if b_col[0]:
            settings.draw_debug_box_color = [int(x * 255) for x in b_col[1]]

        imgui.end()

    def render(self) -> None:
        self.draw_settings_menu()

        imgui.begin("Placeables")

        for ph in self.placeable_helpers:
            imgui.same_line()
            if imgui.button(ph.name):
                self.curr_phelper.on_disable()
                self.curr_phelper = ph
                self.curr_phelper.on_enable()
        self.curr_phelper.post_render(self.pc, self.editor_offset)

        if imgui.button("Save Map"):
            self.save_map(self.load_save_map_name)
        imgui.same_line()
        if imgui.button("Load Map"):
            self.load_map(self.load_save_map_name)
        self.load_save_map_name = imgui.input_text("Save/Load Name", self.load_save_map_name, 20)[1]
        imgui.end()

        imgui.begin("Object Attributes")
        if self.curr_phelper.curr_obj:
            self.curr_phelper.curr_obj.draw()
        imgui.end()

    def enable(self) -> None:
        self.is_in_editor = True
        bl2tools.get_world_info().bPlayersOnly = True
        self.pawn = self.pc.Pawn
        self.pc.HideHUD()
        self.pc.ServerSpectate()
        self.pc.bCollideWorld = False
        self.curr_phelper.on_enable()

        def mouse_input_key(caller: unrealsdk.UObject, function: unrealsdk.UFunction,
                            params: unrealsdk.FStruct) -> bool:
            """
            This function is only hooked to capture LeftMouseButton, RightMouseButton and MouseScroll, without
            having to register any moddedKeybinds.
            :param caller:
            :param function:
            :param params:
            :return:
            """
            if not self.is_in_editor:
                return True
            if params.Event != 0:  # only care for input pressed events
                return True
            if params.key not in ("MouseScrollUp", "MouseScrollDown", "LeftMouseButton", "RightMouseButton"):
                return True

            if params.key == "LeftMouseButton":
                self._left_mouse_button_pressed()
            elif params.key == "RightMouseButton":
                self._right_mouse_button_pressed()
            elif params.key == "MouseScrollUp":
                self._mouse_scroll(1)
            elif params.key == "MouseScrollDown":
                self._mouse_scroll(-1)
            return True

        def post_render(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            canvas = params.Canvas
            canvas.SetPos(20, 20, 0)
            canvas.SetDrawColorStruct((0, 255, 0, 255))
            canvas.DrawText(self.post_render_info_text, False, 2, 2, ())
            return True

        unrealsdk.RegisterHook("WillowGame.WillowUIInteraction.InputKey", __file__, mouse_input_key)
        unrealsdk.RegisterHook("WillowGame.WillowGameViewportClient.PostRender", __file__, post_render)

    def disable(self) -> None:
        self.is_in_editor = False
        bl2tools.get_world_info().bPlayersOnly = False
        self.curr_phelper.on_disable()
        self.pc.Possess(self.pawn, True)
        self.pc.DisplayHUD()
        unrealsdk.RemoveHook("WillowGame.WillowUIInteraction.InputKey", __file__)
        unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.PostRender", __file__)

    def start_loading(self, map_name: str) -> None:
        if not settings.b_editor_mode:
            return
        # when we start to travel it would be good to remove any reference to possibly GC objects

        for helper in self.placeable_helpers:
            helper.cleanup(map_name)

    def end_loading(self, map_name: str) -> None:
        if not settings.b_editor_mode:
            return

        self.pc = bl2tools.get_player_controller()

        for helper in self.placeable_helpers:
            helper.b_setup = True


instance = Editor()
