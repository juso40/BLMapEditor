from time import time
from typing import List, Optional

import unrealsdk
from unrealsdk import *

from .placeablehelper import PlaceableHelper
from .. import bl2tools
from .. import canvasutils
from .. import placeables
from .. import settings


class InterctiveObjectHelper(PlaceableHelper):

    def __init__(self):
        super().__init__(name="Edit InteractiveObject",
                         supported_filters=["All Objects", "Create", "Edited"])

        self.edited_default: dict = {}  # used to restore default attrs

        self.add_as_prefab: List[placeables.AbstractPlaceable] = []  # the placeables you want to save as Prefab
        self.deleted: List[placeables.AbstractPlaceable] = []

        self.curr_preview: Optional[placeables.AbstractPlaceable] = None
        self.delta_time: float = 0.0

    def on_enable(self):
        pass

    def on_disable(self):
        if self.curr_preview:
            self.curr_preview.destroy()
            self.curr_preview = None
        self.curr_obj = None

    def on_command(self, command: str) -> bool:
        cmd_list = command.split()

        if cmd_list[0].lower() == "getscale":
            if self.curr_obj:
                unrealsdk.Log(f"Current Object Scale: {self.curr_obj.get_scale()}")
            else:
                unrealsdk.Log("No Object currently selected in Editor!")
        elif cmd_list[0].lower() == "setscale":
            if self.curr_obj:
                self.curr_obj.set_scale(float(cmd_list[1]))
            else:
                unrealsdk.Log("No Object currently selected in Editor!")
        else:
            return True
        return False

    def add_to_prefab(self) -> None:
        pass

    def add_rotation(self, rotator: tuple) -> None:
        if self.curr_obj:
            self.curr_obj: placeables.AbstractPlaceable
            self.curr_obj.add_rotation(rotator)

    def add_scale(self, scale: float) -> None:
        if self.curr_obj:
            self.curr_obj: placeables.AbstractPlaceable
            self.curr_obj.add_scale(scale)

    def tp_to_selected_object(self, pc: unrealsdk.UObject) -> bool:
        if self.curr_filter == "Create":
            return False
        else:
            pc.Location = tuple(self.objects_by_filter[self.curr_filter][self.object_index].get_location())
            return True

    def restore_objects_defaults(self) -> None:
        if self.curr_filter in ("Create", "Prefab BP"):
            bl2tools.feedback("Reset", "Cannot Reset non existing objects!", 4)
            return

        if self.curr_obj:
            self.curr_obj.restore_default_values(self.edited_default)
            if not self.curr_obj.b_dynamically_created:
                self.objects_by_filter["Edited"].pop(self.objects_by_filter["Edited"].index(self.curr_obj))
                self.object_index %= len(self.objects_by_filter[self.curr_filter])
            self.curr_obj = None

            bl2tools.feedback("Restored", "Successfully restored the objects defaults!", 4)

    def move_object(self, b_move: bool) -> None:

        if self.curr_filter not in ("Create", "Prefab BP"):
            self.curr_obj = self.objects_by_filter[self.curr_filter][self.object_index]
            # add the default values to the default dict to revert changes if needed
            if b_move:
                self.curr_obj.store_default_values(self.edited_default)
                if self.curr_filter != "Prefab Instances" and self.curr_obj not in self.objects_by_filter["Edited"]:
                    self.objects_by_filter["Edited"].append(self.curr_obj)

        elif self.curr_filter in ("Create", "Prefab BP") and b_move:
            # create a new instance from our Blueprint object
            new_instance, created_smcs = self.objects_by_filter[self.curr_filter][self.object_index].instantiate()
            for smc in created_smcs:
                self.objects_by_filter["Edited"].append(smc)
                self.objects_by_filter["All Objects"].append(smc)
            self.curr_obj = new_instance  # let's start editing this new object
            if self.curr_filter == "Prefab BP":
                self.objects_by_filter["Prefab Instances"].append(new_instance)

        if not b_move:
            self.curr_obj = None

    def delete_object(self) -> None:
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
                if not self.objects_by_filter[self.curr_filter]:
                    self.change_filter()
                    self.object_index = 0
                else:
                    self.object_index = (self.object_index - 1) % len(self.objects_by_filter[self.curr_filter])
                bl2tools.feedback("Delete", "Successfully removed the InteractiveObject!", 4)
            except ValueError as e:
                bl2tools.feedback("Delete", str(e), 4)

    def calculate_preview(self) -> None:
        if self.curr_preview:
            self.curr_preview.destroy()
        if self.curr_filter == "Create" and settings.b_show_preview:
            self.curr_preview = self.objects_by_filter["Create"][self.object_index].get_preview()
        else:
            self.curr_preview = None
        self.delta_time = time()

    def post_render(self, canvas: unrealsdk.UObject, pc: unrealsdk.UObject, offset: int, b_pos_locked: bool) -> None:
        if settings.b_show_preview and self.curr_preview:
            x, y, z = canvasutils.rot_to_vec3d([pc.CalcViewRotation.Pitch,
                                                pc.CalcViewRotation.Yaw - canvasutils.u_rotation_180 // 6,
                                                pc.CalcViewRotation.Roll])

            now = time()
            self.curr_preview.set_preview_location((pc.Location.X + x * 200,
                                                    pc.Location.Y + y * 200,
                                                    pc.Location.Z + z * 200))
            self.curr_preview.add_rotation((0,
                                            int((canvasutils.u_rotation_180 / 2.5) * (now - self.delta_time)),
                                            0))
            self.delta_time = now

        if self.curr_obj:
            self.curr_obj.draw_debug_box(pc)
            self.curr_obj.draw_debug_origin(canvas, pc)
            if not b_pos_locked:
                x, y, z = canvasutils.rot_to_vec3d([pc.CalcViewRotation.Pitch,
                                                    pc.CalcViewRotation.Yaw,
                                                    pc.CalcViewRotation.Roll])
                self.curr_obj.set_location((pc.Location.X + offset * x,
                                            pc.Location.Y + offset * y,
                                            pc.Location.Z + offset * z))
        else:
            # Now let us highlight the currently selected object (does not need to be the moved object!)
            if not self.objects_by_filter[self.curr_filter]:
                self.change_filter()
            self.objects_by_filter[self.curr_filter][self.object_index].draw_debug_box(pc)
            self.objects_by_filter[self.curr_filter][self.object_index].draw_debug_origin(canvas, pc)

    def cleanup(self, mapname: str) -> None:
        self.curr_obj = None
        self.curr_preview = None
        self.object_index = 0
        self.objects_by_filter = {f: [] for f in self.available_filters}
        self.edited_default.clear()
        self.add_as_prefab.clear()
        self.deleted.clear()

    def setup(self, mapname: str) -> None:
        if mapname == "menumap" or mapname == "none" or mapname == "":
            return

        self.objects_by_filter["All Objects"].extend([
            placeables.InteractiveObjectBalanceDefinition(
                bl2tools.get_obj_path_name(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                if x.BalanceDefinitionState.BalanceDefinition else
                bl2tools.get_obj_path_name(x.InteractiveObjectDefinition).split(".")[-1],
                x.BalanceDefinitionState.BalanceDefinition
                if x.BalanceDefinitionState.BalanceDefinition else x.InteractiveObjectDefinition,
                x
            )
            for x in unrealsdk.FindAll("WillowInteractiveObject")[1:]]
        )
        self.objects_by_filter["All Objects"].extend([
            placeables.InteractiveObjectBalanceDefinition(
                bl2tools.get_obj_path_name(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                if x.BalanceDefinitionState.BalanceDefinition else
                bl2tools.get_obj_path_name(x.InteractiveObjectDefinition).split(".")[-1],
                x.BalanceDefinitionState.BalanceDefinition
                if x.BalanceDefinitionState.BalanceDefinition else x.InteractiveObjectDefinition,
                x
            )
            for x in unrealsdk.FindAll("WillowVendingMachine")[1:]]
        )
        self.objects_by_filter["All Objects"].extend([
            placeables.InteractiveObjectBalanceDefinition(
                bl2tools.get_obj_path_name(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                if x.BalanceDefinitionState.BalanceDefinition else
                bl2tools.get_obj_path_name(x.InteractiveObjectDefinition).split(".")[-1],
                x.BalanceDefinitionState.BalanceDefinition
                if x.BalanceDefinitionState.BalanceDefinition else x.InteractiveObjectDefinition,
                x
            )
            for x in unrealsdk.FindAll("WillowVendingMachineBlackMarket")[1:]]
        )
        self.objects_by_filter["All Objects"].sort(key=lambda obj: obj.name)
        #############################################################################

        interactives = unrealsdk.FindAll("InteractiveObjectBalanceDefinition")[1:]  # type: list
        do_not_add = tuple(x.DefaultInteractiveObject for x in interactives)
        interactives.extend([x for x in unrealsdk.FindAll("InteractiveObjectDefinition")[1:] if x not in do_not_add])

        this_crashes_so_remove_it = unrealsdk.FindObject("InteractiveObjectBalanceDefinition",
                                                         "GD_Z2_TrailerTrashinData.BalanceDefs.BD_PropaneTank")
        if this_crashes_so_remove_it:
            try:
                interactives.pop(interactives.index(this_crashes_so_remove_it))
            except ValueError:
                pass
            try:
                interactives.pop(interactives.index(this_crashes_so_remove_it.DefaultInteractiveObject))
            except ValueError:
                pass

        self.objects_by_filter["Create"].extend([
            placeables.InteractiveObjectBalanceDefinition(bl2tools.get_obj_path_name(x).split(".")[-1], x)
            for x in interactives]
        )
        self.objects_by_filter["Create"].sort(key=lambda obj: obj.name)

    def load_map(self, map_data: dict) -> None:
        for to_destroy in map_data.get("Destroy", {}).get("InteractiveObjectDefinition", []):
            for placeable in self.objects_by_filter["All Objects"]:  # type: placeables.AbstractPlaceable
                if placeable.holds_object(to_destroy):
                    to_remove = placeable.destroy()
                    for remove_me in to_remove:
                        for _list in self.objects_by_filter.values():
                            try:
                                _list.pop(_list.index(remove_me))
                            except ValueError:
                                pass
                    break

        for bp in map_data.get("Create", {}).get("InteractiveObjectDefinition", []):
            for obj, attrs in bp.items():
                for iodef in self.objects_by_filter["Create"]:  # type: placeables.AbstractPlaceable
                    if iodef.holds_object(obj):
                        new_instance, _ = iodef.instantiate()
                        new_instance.set_location(attrs["Location"])
                        new_instance.set_rotation(attrs["Rotation"])
                        new_instance.set_scale(attrs["Scale"])
                        self.objects_by_filter["Edited"].append(new_instance)
                        self.objects_by_filter["All Objects"].append(new_instance)
                        break

        for obj, attrs in map_data.get("Edit", {}).get("InteractiveObjectDefinition", {}).items():
            for placeable in self.objects_by_filter["All Objects"]:
                if placeable.holds_object(obj):
                    placeable.set_location(attrs["Location"])
                    placeable.set_rotation(attrs["Rotation"])
                    placeable.set_scale(attrs["Scale"])
                    self.objects_by_filter["Edited"].append(placeable)
                    break

    def save_map(self, map_data: dict) -> None:
        for placeable in self.objects_by_filter["All Objects"]:
            placeable.save_to_json(map_data)

        for deleted in self.deleted:
            deleted.save_to_json(map_data)
