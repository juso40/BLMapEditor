import json
import os
from typing import List, cast

import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import placeablehelper
from . import settings

from .. import PyImgui
from ..PyImgui import pyd_imgui

__all__ = ["instance"]


class Editor:
    def __init__(self):
        self.pc: unrealsdk.UObject = None  # The Current PlayerController instance, cached for performance reasons
        self.pawn: unrealsdk.UObject = None  # PlayerPawn instance has to be cached to return to play mode

        self.path: os.PathLike = os.path.dirname(os.path.realpath(__file__))

        self.is_in_editor: bool = False  # Most code will only run while editor mode is active

        self.editing_modes: tuple = ("Move", "Scale", "Rotate")
        self.curr_edit_mode: str = self.editing_modes[0]

        self.rotator_names: tuple = ("Pitch", "Yaw", "Roll")
        self.curr_rot_name: str = self.rotator_names[0]

        # All available Helper Objects, all have the same interface
        self.placeable_helpers: List[placeablehelper.PlaceableHelper] = [placeablehelper.SMCHelper,
                                                                         placeablehelper.PawnHelper,
                                                                         placeablehelper.InteractiveHelper]
        # The currently selected Placeable Helper Mode
        self.curr_phelper: placeablehelper.PlaceableHelper = cast(placeablehelper.PlaceableHelper,
                                                                  self.placeable_helpers[0])

        self.editor_offset: int = 200  # distance between object origin and player

        self.b_move_curr_obj: bool = False  # If true, update position each tick depending on player position/ rotation

        self.is_ctrl_pressed: bool = False  # Needed for Ctrl+[C/V]

        self.frames: List[float] = []  # only used for FPS/Frame time overlay

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
                f"remains unchanged.")
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

    def game_input_pressed(self, key) -> None:
        self.pc = bl2tools.get_player_controller()  # let's rather get the pc each input than each rendered frame
        if key.Name == "Toggle Editor":
            if self.is_in_editor:
                self.disable()
            else:
                self.enable()
            PyImgui.toggle_gui()
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
        self.b_move_curr_obj = False

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
        if not self.b_move_curr_obj:
            self.b_move_curr_obj = True

    def draw_settings_menu(self) -> None:
        """
        Draw the Settings UI Windoww. Populated with various Editor Specific values.
        Most settings will be saved using the SDK SaveModSettings() function.

        :return:
        """
        pyd_imgui.begin("Settings")

        settings.b_lock_object_position = pyd_imgui.checkbox("Lock Object Position", settings.b_lock_object_position)[1]
        pyd_imgui.same_line()
        preview_checked = pyd_imgui.checkbox("Show Preview", settings.b_show_preview)
        if preview_checked[0]:
            settings.b_show_preview = preview_checked[1]
            self.curr_phelper.calculate_preview()

        self.pc.SpectatorCameraSpeed = pyd_imgui.slider_float("Camera-Speed", self.pc.SpectatorCameraSpeed, 0, 20000)[1]
        self.editor_offset = pyd_imgui.slider_float("Camera-Object Distance", self.editor_offset, 0, 2000)[1]
        settings.editor_grid_size = pyd_imgui.slider_float("Grid Size", settings.editor_grid_size, 0, 500)[1]

        b_col = pyd_imgui.color_edit3("Debug Box Color", [x / 255 for x in settings.draw_debug_box_color],
                                      pyd_imgui.COLOR_EDIT_FLAGS_PICKER_HUE_BAR)

        if b_col[0]:
            settings.draw_debug_box_color = [int(x * 255) for x in b_col[1]]

        # Debug Origin Slider not worth it
        # To use my current methods i need access to the Games Canvas

        # b_col = pyd_imgui.color_edit3("Debug Origin Color",
        #                               [x / 255 for x in settings.draw_debug_origin_color][2::-1],
        #                               pyd_imgui.COLOR_EDIT_FLAGS_PICKER_HUE_BAR)
        # if b_col[0]:
        #     settings.draw_debug_origin_color_color = tuple((list(*(int(x * 255) for x in b_col[1]))[::-1], 255))

        pyd_imgui.end()

    def render(self) -> None:
        self.draw_settings_menu()

        pyd_imgui.begin("Placeables")
        if pyd_imgui.begin_tab_bar("##Placeables"):
            for ph in self.placeable_helpers:
                if pyd_imgui.tab_item_button(ph.name):
                    self.curr_phelper.on_disable()
                    self.curr_phelper = ph
                    self.curr_phelper.on_enable()
            pyd_imgui.end_tab_bar()
        self.curr_phelper.post_render(self.pc, self.editor_offset)

        if pyd_imgui.button("Save Map"):
            self.save_map(self.load_save_map_name)
        pyd_imgui.same_line()
        if pyd_imgui.button("Load Map"):
            self.load_map(self.load_save_map_name)
        self.load_save_map_name = pyd_imgui.input_text("Save/Load Name", self.load_save_map_name, 20)[1]
        pyd_imgui.end()

        pyd_imgui.begin("Object Attributes")
        if self.curr_phelper.curr_obj:
            self.curr_phelper.curr_obj.draw()
        pyd_imgui.end()

    def enable(self) -> None:
        self.is_in_editor = True
        bl2tools.get_world_info().bPlayersOnly = True
        self.pawn = self.pc.Pawn
        self.pc.HideHUD()
        self.pc.ServerSpectate()
        self.pc.bCollideWorld = False
        self.curr_phelper.on_enable()

        PyImgui.subscribe_end_scene(self.render)

    def disable(self) -> None:
        self.is_in_editor = False
        bl2tools.get_world_info().bPlayersOnly = False
        self.curr_phelper.on_disable()
        self.pc.Possess(self.pawn, True)
        self.pc.DisplayHUD()

        PyImgui.unsubscribe_end_scene(self.render)

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
