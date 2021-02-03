import json
import os
from itertools import cycle
from time import time
from typing import Dict, List, cast

import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import canvasutils
from . import commands
from . import placeables
from . import settings

__all__ = ["instance"]


class Editor:
    def __init__(self):
        self.pc: unrealsdk.UObject = None

        commands.instance.add_command("mapeditor", self.commands)
        self.path: os.PathLike = os.path.dirname(os.path.realpath(__file__))

        self.is_in_editor: bool = False
        self.pawn: unrealsdk.UObject = None

        self.edit_modes: cycle = cycle(["Move", "Scale", "Rotate"])
        self.curr_edit_mode = next(self.edit_modes)

        self.rotator_names: cycle = cycle(["Pitch", "Yaw", "Roll"])
        self.curr_rot_name: str = next(self.rotator_names)

        self.b_move_curr_obj: bool = False
        self.b_lock_curr_obj_loc: bool = False
        self.curr_obj: placeables.AbstractPlaceable = None
        self.object_index: int = 0
        self.default_editor_offset: int = 200
        self.editor_offset: int = self.default_editor_offset

        self.filter_names: cycle = cycle(["All Components", "Edited", "Create", "Prefab BP", "Prefab Instances"])
        self.curr_filter: str = next(self.filter_names)
        self.objects_by_filter: Dict[str, List[placeables.AbstractPlaceable]] = {"All Components": [],
                                                                                 "Edited": [],
                                                                                 "Create": [],
                                                                                 "Prefab BP": [],
                                                                                 "Prefab Instances": []}

        self.edited_default: dict = {}  # used to restore default attrs
        self.deleted: List[placeables.AbstractPlaceable] = []

        self.add_as_prefab: List[placeables.AbstractPlaceable] = []  # the placeables you want to save as Prefab

        self.curr_preview: placeables.AbstractPlaceable = None
        self.delta_time: float = 0.0

    def commands(self, arguments: str) -> bool:
        arguments = arguments.split()
        if arguments[0].lower() == "speed":
            self.pc = bl2tools.get_player_controller()
            self.pc.SpectatorCameraSpeed = int(arguments[1])
        elif arguments[0].lower() == "getscale":
            if self.curr_obj:
                unrealsdk.Log(f"Current Object Scale: {self.curr_obj.get_scale()}")
            else:
                unrealsdk.Log("No Object currently selected in Editor!")
        elif arguments[0].lower() == "setscale":
            if self.curr_obj:
                self.curr_obj.set_scale(float(arguments[1]))
            else:
                unrealsdk.Log("No Object currently selected in Editor!")
        elif arguments[0].lower() == "save":
            self.save_map(arguments[1])
        elif arguments[0].lower() == "load":
            self.load_map(arguments[1])
        elif arguments[0].lower() == "clearprefab":
            self.add_as_prefab.clear()
        elif arguments[0].lower() == "addtoprefab":
            if self.curr_filter not in ("Create", "Prefab BP", "Prefab Instances"):
                self.add_as_prefab.append(self.objects_by_filter[self.curr_filter][self.object_index])
        elif arguments[0].lower() == "removefromprefab":
            if self.curr_filter not in ("Create", "Prefab BP", "Prefab Instances"):
                try:
                    self.add_as_prefab.pop(
                        self.add_as_prefab.index(self.objects_by_filter[self.curr_filter][self.object_index])
                    )
                    unrealsdk.Log("Removed")
                except ValueError:
                    unrealsdk.Log("Currently selected object was not part of the prefab.")
        elif arguments[0].lower() == "saveprefab":
            if not self.add_as_prefab:
                unrealsdk.Log("No Components have been selected, can't create empty Prefab!")
                return False
            new_prefab_bp = placeables.Prefab.create_prefab_from_smc(self.add_as_prefab, arguments[1])
            self.curr_obj = None  # we only have created a Prefab BP, no instance has been created
            self.objects_by_filter["Prefab BP"].append(new_prefab_bp)
            unrealsdk.Log(f"Saved Prefab as prefab_{arguments[1]}.json!")
            self.add_as_prefab.clear()
        elif arguments[0].lower() == "loadprefab":
            new_prefab_bp = placeables.Prefab.load_prefab_json(arguments[1])
            if new_prefab_bp:
                self.objects_by_filter["Prefab BP"].append(new_prefab_bp)
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
                "load <name> -> load mapchanges for this map from <name>.json")
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

        for uclass, to_destroy in load_this.get("Destroy", {}).items():
            for uobject in to_destroy:
                for placeable in self.objects_by_filter["All Components"]:  # type: placeables.AbstractPlaceable
                    if placeable.holds_object(uobject):
                        placeable.destroy()
                        break

        for uclass, to_create in load_this.get("Create", {}).items():
            for bp in to_create:
                for obj, attrs in bp.items():
                    if uclass == "StaticMesh":
                        for smc_bp in self.objects_by_filter["Create"]:  # type: placeables.AbstractPlaceable
                            if smc_bp.holds_object(obj):
                                new_instance, created_smcs = smc_bp.instantiate()
                                new_instance.set_location(attrs["Location"])
                                new_instance.set_rotation(attrs["Rotation"])
                                new_instance.set_scale(attrs["Scale"])
                                self.objects_by_filter["Edited"].append(new_instance)
                                self.objects_by_filter["All Components"].append(new_instance)
                                break

        for uclass, to_edit in load_this.get("Edit", {}).items():
            for obj, attrs in to_edit.items():
                if uclass == "StaticMeshComponent":
                    for placeable in self.objects_by_filter["All Components"]:
                        if placeable.holds_object(obj):
                            placeable.set_location(attrs["Location"])
                            placeable.set_rotation(attrs["Rotation"])
                            placeable.set_scale(attrs["Scale"])
                            self.objects_by_filter["Edited"].append(placeable)
                            break

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
        for placeable in self.objects_by_filter["All Components"]:
            placeable.save_to_json(save_this[curr_map])

        for deleted in self.deleted:
            deleted.save_to_json(save_this[curr_map])

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
            self.curr_rot_name = next(self.rotator_names)
            self.safe_feedback("Map Editor", self.curr_rot_name, 4)
        elif key.Name == "Lock Obj in Place":
            self.b_lock_curr_obj_loc = not self.b_lock_curr_obj_loc
            self.safe_feedback("Map Editor",
                               f"Current Object Position is now "
                               f"{'locked' if self.b_lock_curr_obj_loc else 'unlocked'}!",
                               4)
        elif key.Name == "Delete Obj":
            self._delete_object()
        elif key.Name == "Add/Remove to/from Prefab":
            if self.curr_filter not in ("Create", "Prefab BP", "Prefab Instances"):
                try:
                    self.add_as_prefab.pop(
                        self.add_as_prefab.index(self.objects_by_filter[self.curr_filter][self.object_index])
                    )
                    self.safe_feedback("Prefab Add/Remove", "Removed selected object from Prefab", 4)
                except ValueError:
                    self.add_as_prefab.append(self.objects_by_filter[self.curr_filter][self.object_index])
                    self.safe_feedback("Prefab Add/Remove", "Added selected object to Prefab", 4)
            else:
                self.safe_feedback("Prefab Add/Remove", "Can only add SMC to Prefab!", 4)

    def _tp_to_selected_object(self) -> None:
        """
        This function gets called for the "TP to Obj" keybind.
        If we are in "Create" or in "Prefabs" filter, don't do anything and tell the user.
        :return:
        """
        if self.curr_filter in ("Create", "Prefab BP"):
            self.safe_feedback("TP To Object", "Can not TP to non existing objects!", 4)
        else:
            self.pc.Location = tuple(self.objects_by_filter[self.curr_filter][self.object_index].get_location())
            self.safe_feedback("TP To Object", "Successfully TP'd to the object.", 4)

    def _change_filter(self) -> None:
        """
        This function gets called if the "Filter Editor" keybinds gets triggered.
        Let's cycle between our filters, if needed fill the lists with new data.
        :return:
        """
        if self.b_move_curr_obj:  # we don't want to switch object filter while moving an object
            return

        # the important stuff

        self.curr_obj = None
        self.curr_filter = next(self.filter_names)

        while not self.objects_by_filter[self.curr_filter]:  # Edited/prefabs may be empty
            self.curr_filter = next(self.filter_names)
        self.object_index = 0
        self.safe_feedback(self.curr_filter, "Cycled filter!", 4)

        self._calculate_preview()

    def _calculate_preview(self):
        if self.curr_preview:
            self.curr_preview.destroy()
        if self.curr_filter == "Create" and settings.b_show_preview:
            self.curr_preview = self.objects_by_filter["Create"][self.object_index].get_preview()
        else:
            self.curr_preview = None
        self.delta_time = time()

    def _change_edit_mode(self) -> None:
        """
        Cycle between the available edit modes.
        After switching to next mode, give the user feedback.

        :return:
        """
        if not self.b_move_curr_obj:  # we only cycle between edit modes while actually editing an obj
            return

        self.curr_edit_mode = next(self.edit_modes)
        self.safe_feedback(self.curr_edit_mode, "Cycled edit mode!", 4)

    def _restore_objects_default(self) -> None:
        """
        docstring...
        :return:
        """
        if self.curr_filter in ("Create", "Prefab BP"):
            self.safe_feedback("Reset", "Cannot Reset non existing objects!", 4)
            return

        if self.curr_obj and self.b_move_curr_obj:
            self.curr_obj.restore_default_values(self.edited_default)
            if not self.curr_obj.b_dynamically_created:
                self.objects_by_filter["Edited"].pop(self.objects_by_filter["Edited"].index(self.curr_obj))
                self.object_index %= len(self.objects_by_filter[self.curr_filter])
                self.curr_obj = None
                self.b_move_curr_obj = False

            self.safe_feedback("Restored", "Successfully restored the objects defaults!", 4)
            return

    def _move_object(self) -> None:
        """
        This function gets Triggered on the "Move Object" input.
        Add the current moved object to the edited_default dict to revert changes.
        While we are in "Create" filter, we need to create a new SMC before moving it.
        :return:
        """
        self.b_move_curr_obj = not self.b_move_curr_obj

        if self.curr_filter not in ("Create", "Prefab BP"):
            self.curr_obj = self.objects_by_filter[self.curr_filter][self.object_index]
            # add the default values to the default dict to revert changes if needed
            if self.b_move_curr_obj:
                self.curr_obj.store_default_values(self.edited_default)
                if self.curr_filter != "Prefab Instances" and self.curr_obj not in self.objects_by_filter["Edited"]:
                    self.objects_by_filter["Edited"].append(self.curr_obj)

        elif self.curr_filter in ("Create", "Prefab BP") and self.b_move_curr_obj:
            # create a new instance from our Blueprint object
            new_instance, created_smcs = self.objects_by_filter[self.curr_filter][self.object_index].instantiate()
            for smc in created_smcs:
                self.objects_by_filter["Edited"].append(smc)
                self.objects_by_filter["All Components"].append(smc)
            self.curr_obj = new_instance  # let's start editing this new object
            if self.curr_filter == "Prefab BP":
                self.objects_by_filter["Prefab Instances"].append(new_instance)

        if not self.b_move_curr_obj:
            self.curr_obj = None

    def _delete_object(self) -> None:
        """
        This function gets Triggered on the "Delete Obj" input.
        If an object is selected and was not a created object, delete it, add that change to the "edited_objects" dict.

        :return:
        """

        if self.curr_obj:
            try:
                to_remove = self.curr_obj.destroy()
                for remove_me in to_remove:
                    for _list in self.objects_by_filter.values():
                        try:
                            _list.pop(_list.index(remove_me))
                        except ValueError:
                            pass

                if not self.curr_obj.b_dynamically_created and self.curr_obj not in self.deleted:
                    self.deleted.append(self.curr_obj)
                self.curr_obj = None
                self.b_move_curr_obj = False
                if not self.objects_by_filter[self.curr_filter]:
                    self._change_filter()
                    self.object_index = 0
                else:
                    self.object_index = (self.object_index - 1) % len(self.objects_by_filter[self.curr_filter])
                self.safe_feedback("Delete", "Successfully removed the SMC!", 4)
            except ValueError as e:
                self.safe_feedback("Delete", str(e), 4)
            # after deleting the last existing "edited" item, then we don't have anything to show, so change the
            # filter

    def enable(self) -> None:
        self.is_in_editor = True
        self.pawn = self.pc.Pawn
        self.pc.ServerSpectate()
        self.pc.bCollideWorld = False

        def post_render(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if not params.Canvas:
                return True

            # draw useful information to screen, like current filter, current mesh name, b_lock_curr_pos
            canvasutils.draw_text(params.Canvas,
                                  f"Editing Filter: {self.curr_filter}\n"
                                  f"Current Object Position Locked: {self.b_lock_curr_obj_loc}\n"
                                  f"Editor Offset: {self.editor_offset}\n"
                                  f"Editor Speed: {self.pc.SpectatorCameraSpeed}\n"
                                  f"Selecting Object {self.object_index}/"
                                  f"{len(self.objects_by_filter[self.curr_filter]) - 1}\n"
                                  f"Editing Rotation: {self.curr_rot_name}\n"
                                  f"Current Editor Mode: {self.curr_edit_mode}\n"
                                  f"Show Preview: {settings.b_show_preview}\n",
                                  20, 20,
                                  settings.draw_debug_editor_info_scale,
                                  settings.draw_debug_editor_info_scale,
                                  settings.draw_debug_editor_info_color)

            if settings.b_show_preview and self.curr_preview:
                x, y, z = canvasutils.rot_to_vec3d([self.pc.CalcViewRotation.Pitch,
                                                    self.pc.CalcViewRotation.Yaw - canvasutils.u_rotation_180 // 6,
                                                    self.pc.CalcViewRotation.Roll])

                now = time()
                self.curr_preview.set_preview_location((self.pc.Location.X + x * 200,
                                                        self.pc.Location.Y + y * 200,
                                                        self.pc.Location.Z + z * 200))
                self.curr_preview.add_rotation((0,
                                                int((canvasutils.u_rotation_180 / 2.5) * (now - self.delta_time)),
                                                0))
                self.delta_time = now

            # highlight the currently selected prefab meshes
            for prefab_data in self.add_as_prefab:
                prefab_data.draw_debug_box(self.pc)

            if self.b_move_curr_obj:
                if not self.b_lock_curr_obj_loc:
                    x, y, z = canvasutils.rot_to_vec3d([self.pc.CalcViewRotation.Pitch,
                                                        self.pc.CalcViewRotation.Yaw,
                                                        self.pc.CalcViewRotation.Roll])
                    self.curr_obj.set_location((self.pc.Location.X + self.editor_offset * x,
                                                self.pc.Location.Y + self.editor_offset * y,
                                                self.pc.Location.Z + self.editor_offset * z))

            if self.curr_obj:
                self.curr_obj.draw_debug_box(self.pc)
                self.curr_obj.draw_debug_origin(params.Canvas, self.pc)
            else:
                # Now let us highlight the currently selected object (does not need to be the moved object!)
                if not self.objects_by_filter[self.curr_filter]:
                    self._change_filter()
                self.objects_by_filter[self.curr_filter][self.object_index].draw_debug_box(self.pc)
                self.objects_by_filter[self.curr_filter][self.object_index].draw_debug_origin(params.Canvas, self.pc)

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
                    if self.curr_filter not in ("Prefab BP", "Prefab Instances"):
                        self.curr_obj.add_scale(0.05)
                elif params.key == "MouseScrollDown":
                    if self.curr_filter not in ("Prefab BP", "Prefab Instances"):
                        self.curr_obj.add_scale(-0.05)
            elif self.curr_edit_mode == "Rotate" and self.b_move_curr_obj:
                if params.key == "MouseScrollUp":
                    self.curr_obj.add_rotation(
                        [canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Pitch" else 0,
                         canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Yaw" else 0,
                         canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Roll" else 0, ]
                    )

                elif params.key == "MouseScrollDown":
                    self.curr_obj.add_rotation(
                        [-canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Pitch" else 0,
                         -canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Yaw" else 0,
                         -canvasutils.u_rotation_180 // 180 if self.curr_rot_name == "Roll" else 0, ]
                    )

            elif params.key == "MouseScrollUp":
                self.object_index = (self.object_index - 1) % len(self.objects_by_filter[self.curr_filter])
                self.show_selected_obj(self.curr_filter, self.objects_by_filter[self.curr_filter],
                                       self.object_index)
                self._calculate_preview()
            elif params.key == "MouseScrollDown":
                self.object_index = (self.object_index + 1) % len(self.objects_by_filter[self.curr_filter])
                self.show_selected_obj(self.curr_filter, self.objects_by_filter[self.curr_filter],
                                       self.object_index)
                self._calculate_preview()

            return True

        unrealsdk.RegisterHook("WillowGame.WillowGameViewportClient.PostRender", __file__, post_render)
        unrealsdk.RegisterHook("WillowGame.WillowUIInteraction.InputKey", __file__, handle_input)

    def disable(self) -> None:
        self.is_in_editor = False
        self.curr_obj = None
        if self.curr_preview:
            self.curr_preview.destroy()
            self.curr_preview = None

        self.pc.Possess(self.pawn, True)

        unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.PostRender", __file__)
        unrealsdk.RemoveHook("WillowGame.WillowUIInteraction.InputKey", __file__)

    def start_loading(self, map_name: str) -> None:
        # when we start to travel it would be good to remove any reference to possibly GC objects
        self.object_index = 0
        self.deleted.clear()
        self.edited_default.clear()
        self.objects_by_filter["All Components"].clear()
        self.objects_by_filter["Edited"].clear()
        self.objects_by_filter["Create"].clear()
        self.objects_by_filter["Prefab BP"].clear()
        self.objects_by_filter["Prefab Instances"].clear()

    def end_loading(self, map_name: str) -> None:
        if map_name == "menumap" or map_name == "none" or map_name == "":
            return
        self.pc = bl2tools.get_player_controller()

        for x in unrealsdk.FindAll("StaticMeshCollectionActor"):
            self.objects_by_filter["All Components"].extend([
                placeables.StaticMeshComponent(bl2tools.get_obj_path_name(y.StaticMesh).split(".", 1)[-1],
                                               y.StaticMesh, y) for y in x.AllComponents]
            )
        self.objects_by_filter["All Components"].sort(key=lambda obj: obj.name)

        for mesh in unrealsdk.FindAll("StaticMesh")[1:]:
            self.objects_by_filter["Create"].append(
                placeables.StaticMeshComponent(bl2tools.get_obj_path_name(mesh).split(".", 1)[-1], mesh)
            )
        self.objects_by_filter["Create"].sort(key=lambda _x: _x.name)

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
