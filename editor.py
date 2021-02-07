import json
import os
from typing import List, cast

import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import canvasutils
from . import commands
from . import placeablehelper
from . import settings

__all__ = ["instance"]


class Editor:
    def __init__(self):
        self.pc: unrealsdk.UObject = None

        commands.instance.add_command("mapeditor", self.commands)
        self.path: os.PathLike = os.path.dirname(os.path.realpath(__file__))

        self.is_in_editor: bool = False
        self.pawn: unrealsdk.UObject = None

        self.editing_modes: tuple = ("Move", "Scale", "Rotate")
        self.curr_edit_mode: str = self.editing_modes[0]

        self.rotator_names: tuple = ("Pitch", "Yaw", "Roll")
        self.curr_rot_name: str = self.rotator_names[0]

        self.placeable_helpers: List[placeablehelper.PlaceableHelper] = [placeablehelper.SMCHelper,
                                                                         placeablehelper.PawnHelper,
                                                                         placeablehelper.InteractiveHelper]
        self.curr_phelper: placeablehelper.PlaceableHelper = cast(placeablehelper.PlaceableHelper,
                                                                  self.placeable_helpers[0])

        self.default_editor_offset: int = 200
        self.editor_offset: int = self.default_editor_offset

        self.b_lock_pos: bool = False
        self.b_move_curr_obj: bool = False

    def commands(self, arguments: str) -> bool:
        if not self.curr_phelper.on_command(arguments):
            return False

        arguments = arguments.split()
        if arguments[0].lower() == "speed":
            self.pc = bl2tools.get_player_controller()
            self.pc.SpectatorCameraSpeed = int(arguments[1])
        elif arguments[0].lower() == "save":
            self.save_map(arguments[1])
        elif arguments[0].lower() == "load":
            self.load_map(arguments[1])
        elif arguments[0].lower() == "offset":
            try:
                self.editor_offset = int(arguments[1])
            except ValueError:
                unrealsdk.Log("Editor Offset only takes Integers.")
        elif arguments[0].lower() == "help":
            unrealsdk.Log(
                "Map Editor Help:\n"
                "Left Mouse Button -> Start/Stop editing the currently selected object\n"
                "Right Mouse Button -> Cycle between Filters/Modes\n"
                "Mousewheel Up/Down -> Scroll trough available objects while no Object is selected for editing, "
                "change object size/rotation/scale depening on current editor mode while an "
                "object is selected for editing\n"
                "Supported Commands (always start with 'mapeditor '):\n"
                "help -> show this message\n"
                "speed <int> -> change the editor camera speed\n"
                "getscale -> get the currently selected objects Scale\n"
                "setscale <float> -> change the currently selected objects Scale\n"
                "offset <int> change the objects offset/distance from your camera in edit mode\n"
                "loadprefab <name> -> load an existing prefab from your Prefabs folder\n"
                "saveprefab <name> -> save your currently selected SMCs into one Prefab\n"
                "clearprefab -> clear all of your currently selected SMCs from your Prefab selection\n"
                "save <name> -> Save the current edits to this map into a <name>.json file\n"
                "load <name> -> load mapchanges for this map from <name>.json\n"
            )
        else:
            return True
        return False

    def load_map(self, name: str) -> None:
        curr_map = bl2tools.get_world_info().GetStreamingPersistentMapName().lower()
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
            helper.load_map(load_this)

    def save_map(self, name: str) -> None:
        curr_map = bl2tools.get_world_info().GetStreamingPersistentMapName().lower()
        save_this = {}

        try:
            with open(os.path.join(self.path, "Maps", f"{name}.json")) as fp:
                save_this = json.load(fp)
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
        self.pc = bl2tools.get_player_controller()  # let's rather get he pc each input than each rendered frame
        if key.Name == "Toggle Editor":
            if self.is_in_editor:
                self.disable()
            else:
                self.enable()
        elif not self.is_in_editor:
            return

        elif key.Name == "Change Editor Mode":
            self.curr_phelper.on_disable()
            self.curr_phelper = self.placeable_helpers[
                (self.placeable_helpers.index(self.curr_phelper) + 1) % len(self.placeable_helpers)
                ]
            self.curr_phelper.on_enable()
        elif key.Name == "Add/Remove to/from Prefab":
            self.curr_phelper.add_to_prefab()
        elif key.Name == "Toggle Preview":
            settings.b_show_preview = not settings.b_show_preview
            self._calculate_preview()
        elif key.Name == "TP To Object":
            self._tp_to_selected_object()
        elif key.Name == "TP my Pawn to me":
            self.pawn.Location = (self.pc.Location.X, self.pc.Location.Y, self.pc.Location.Z)
        elif key.Name == "Restore Object Defaults":
            self._restore_objects_default()
        elif key.Name == "Editor Offset Reset":  # reset the distance from cam to object to the default value
            self.editor_offset = self.default_editor_offset
        elif key.Name == "Cycle Pitch|Yaw|Roll":
            self.curr_rot_name = self.rotator_names[
                (self.rotator_names.index(self.curr_rot_name) + 1) % len(self.rotator_names)
                ]
            self.safe_feedback("Map Editor", self.curr_rot_name, 4)
        elif key.Name == "Lock Obj in Place":
            self.b_lock_pos = not self.b_lock_pos
            self.safe_feedback("Map Editor",
                               f"Current Object Position is now "
                               f"{'locked' if self.b_lock_pos else 'unlocked'}!",
                               4)
        elif key.Name == "Delete Obj":
            self._delete_object()

    def _tp_to_selected_object(self) -> None:
        """
        This function gets called for the "TP to Obj" keybind.
        If we are in "Create" or in "Prefabs" filter, don't do anything and tell the user.
        :return:
        """
        self.curr_phelper.tp_to_selected_object(self.pc)

    def _change_filter(self) -> None:
        """
        This function gets called if the "Filter Editor" keybinds gets triggered.
        Let's cycle between our filters, if needed fill the lists with new data.
        :return:
        """
        if self.b_move_curr_obj:  # we don't want to switch object filter while moving an object
            return

        self.curr_phelper.change_filter()
        self.safe_feedback(self.curr_phelper.get_filter(), "Changed Filter", 4)

    def _calculate_preview(self):
        self.curr_phelper.calculate_preview()

    def _change_edit_mode(self) -> None:
        """
        Cycle between the available edit modes.
        After switching to next mode, give the user feedback.

        :return:
        """
        if not self.b_move_curr_obj:  # we only cycle between edit modes while actually editing an obj
            return

        self.curr_edit_mode = self.editing_modes[
            (self.editing_modes.index(self.curr_edit_mode) + 1) % len(self.editing_modes)
            ]
        self.safe_feedback(self.curr_edit_mode, "Cycled edit mode!", 4)

    def _restore_objects_default(self) -> None:
        """
        docstring...
        :return:
        """
        self.curr_phelper.restore_objects_defaults()
        self.b_move_curr_obj = False

    def _move_object(self) -> None:
        """
        This function gets Triggered on the "Move Object" input.
        Add the current moved object to the edited_default dict to revert changes.
        While we are in "Create" filter, we need to create a new SMC before moving it.
        :return:
        """
        self.b_move_curr_obj = not self.b_move_curr_obj
        self.curr_phelper.move_object(self.b_move_curr_obj)

    def _delete_object(self) -> None:
        """
        This function gets Triggered on the "Delete Obj" input.
        If an object is selected and was not a created object, delete it, add that change to the "edited_objects" dict.

        :return:
        """
        self.curr_phelper.delete_object()
        self.b_move_curr_obj = False

    def enable(self) -> None:
        self.is_in_editor = True
        self.pawn = self.pc.Pawn
        self.pc.ServerSpectate()
        self.pc.bCollideWorld = False
        self.curr_phelper.on_enable()

        def post_render(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if not params.Canvas:
                return True

            # draw useful information to screen, like current filter, current mesh name, b_lock_curr_pos
            canvasutils.draw_text(params.Canvas,
                                  f"Editor Mode: {self.curr_phelper.name}\n"
                                  f"Editing Filter: {self.curr_phelper.get_filter()}\n"
                                  f"Current Object Position Locked: {self.b_lock_pos}\n"
                                  f"Editor Offset: {self.editor_offset}\n"
                                  f"Editor Speed: {self.pc.SpectatorCameraSpeed}\n"
                                  f"Selecting Object {self.curr_phelper.get_index_of_total()}\n"
                                  f"Editing Rotation: {self.curr_rot_name}\n"
                                  f"Editing Mode: {self.curr_edit_mode}\n"
                                  f"Show Preview: {settings.b_show_preview}\n",
                                  20, 20,
                                  settings.draw_debug_editor_info_scale,
                                  settings.draw_debug_editor_info_scale,
                                  settings.draw_debug_editor_info_color)

            self.curr_phelper.post_render(params.Canvas, self.pc, self.editor_offset, self.b_lock_pos)
            return True

        def handle_input(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:

            """
            This function is only hooked to capture LeftMouseButton, RightMouseButton and MouseScroll, without
            having to register any moddedKeybinds.
            :param caller:
            :param function:
            :param params:
            :return:
            """
            if params.Event != 0:  # only care for input pressed events
                return True

            if params.key not in ("MouseScrollUp", "MouseScrollDown", "LeftMouseButton", "RightMouseButton"):
                return True

            if params.key == "LeftMouseButton":
                self._move_object()
            elif params.key == "RightMouseButton":
                self._change_filter()
                self._change_edit_mode()

            if self.curr_edit_mode == "Move" and self.b_move_curr_obj:
                if params.key == "MouseScrollUp":
                    self.editor_offset += 20
                elif params.key == "MouseScrollDown":
                    self.editor_offset -= 20
            elif self.curr_edit_mode == "Scale" and self.b_move_curr_obj:
                if params.key == "MouseScrollUp":
                    self.curr_phelper.add_scale(0.05)
                elif params.key == "MouseScrollDown":
                    self.curr_phelper.add_scale(-0.05)
            elif self.curr_edit_mode == "Rotate" and self.b_move_curr_obj:
                if params.key == "MouseScrollUp":
                    self.curr_phelper.add_rotation(
                        (canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Pitch" else 0,
                         canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Yaw" else 0,
                         canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Roll" else 0)
                    )

                elif params.key == "MouseScrollDown":
                    self.curr_phelper.add_rotation(
                        (-canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Pitch" else 0,
                         -canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Yaw" else 0,
                         -canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Roll" else 0)
                    )

            elif params.key == "MouseScrollUp":
                _filter, _obj_list, _index = self.curr_phelper.index_down()
                self.show_selected_obj(_filter, _obj_list, _index)
                self._calculate_preview()
            elif params.key == "MouseScrollDown":
                _filter, _obj_list, _index = self.curr_phelper.index_up()
                self.show_selected_obj(_filter, _obj_list, _index)
                self._calculate_preview()

            return True

        unrealsdk.RegisterHook("WillowGame.WillowGameViewportClient.PostRender", __file__, post_render)
        unrealsdk.RegisterHook("WillowGame.WillowUIInteraction.InputKey", __file__, handle_input)

    def disable(self) -> None:
        self.is_in_editor = False
        self.curr_phelper.on_disable()

        self.pc.Possess(self.pawn, True)

        unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.PostRender", __file__)
        unrealsdk.RemoveHook("WillowGame.WillowUIInteraction.InputKey", __file__)

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
            helper.setup(map_name)

    def show_selected_obj(self, title, show_from, index):
        feedback = ""

        size = len(show_from)
        for o in range(index - 3, index + 4):
            if show_from[o % size] == show_from[index]:
                feedback += f"<font color=\"#A83232\">{show_from[o % size].name}</font>\n"
            else:
                feedback += f"{show_from[o % size].name}\n"
        self.safe_feedback(title, feedback, 4)

    def safe_feedback(self, title: str, feedback: str, duration: int) -> None:
        if self.pc.GetHUDMovie() is None:
            _loc = (self.pc.Location.X, self.pc.Location.Y, self.pc.Location.Z)
            _rot = (self.pc.Rotation.Pitch, self.pc.Rotation.Yaw, self.pc.Rotation.Roll)
            self.pc.Possess(self.pawn, True)
            self.pc.DisplayHUD()
            self.pawn = self.pc.Pawn
            self.pc.ServerSpectate()
            self.pc.bCollideWorld = False
            self.pc.Rotation = _rot
            self.pc.Location = _loc

        bl2tools.feedback(title, feedback, duration)


instance = Editor()
