from math import radians, tan
from time import time
from typing import List

import unrealsdk
from unrealsdk import *

from .placeablehelper import PlaceableHelper
from .. import bl2tools
from .. import canvasutils
from .. import placeables
from .. import settings


class InterctiveObjectHelper(PlaceableHelper):

    def __init__(self):
        super().__init__(name="Edit InteractiveObject", supported_filters=["All Objects", "Create", "Edited"])

        self.edited_default: dict = {}  # used to restore default attrs

        self.add_as_prefab: List[placeables.AbstractPlaceable] = []  # the placeables you want to save as Prefab
        self.deleted: List[placeables.AbstractPlaceable] = []

    def on_enable(self) -> None:
        super(InterctiveObjectHelper, self).on_enable()

    def on_disable(self) -> None:
        super(InterctiveObjectHelper, self).on_disable()

    def add_to_prefab(self) -> None:
        pass

    def get_filter(self) -> str:
        return super().get_filter()

    def get_index_of_total(self) -> str:
        return super().get_index_of_total()

    def add_rotation(self, rotator: tuple) -> None:
        super(InterctiveObjectHelper, self).add_rotation(rotator)

    def add_scale(self, scale: float) -> None:
        super(InterctiveObjectHelper, self).add_scale(scale)

    def tp_to_selected_object(self, pc: unrealsdk.UObject) -> bool:
        if self.curr_filter == "Create":
            return False
        else:
            pc.Location = tuple(self._cached_objects_for_filter[self.object_index].get_location())
            return True

    def restore_objects_defaults(self) -> None:
        if self.curr_filter in ("Create", "Prefab BP"):
            bl2tools.feedback("Reset", "Cannot Reset non existing objects!", 4)
            return

        if self.curr_obj:
            self.curr_obj.restore_default_values(self.edited_default)
            if not self.curr_obj.b_dynamically_created:
                self.objects_by_filter["Edited"].pop(self.objects_by_filter["Edited"].index(self.curr_obj))
                self.object_index %= len(self._cached_objects_for_filter)
            self.curr_obj = None

            bl2tools.feedback("Restored", "Successfully restored the objects defaults!", 4)
        self.is_cache_dirty = True

    def move_object(self) -> None:
        if self.curr_obj:
            self.curr_obj = None
        else:
            if self.curr_filter not in ("Create", "Prefab BP"):
                self.curr_obj = self._cached_objects_for_filter[self.object_index]
                # add the default values to the default dict to revert changes if needed
                self.curr_obj.store_default_values(self.edited_default)
                if self.curr_filter != "Prefab Instances" and self.curr_obj not in self.objects_by_filter["Edited"]:
                    self.objects_by_filter["Edited"].append(self.curr_obj)

            elif self.curr_filter in ("Create", "Prefab BP"):
                # create a new instance from our Blueprint object
                new_instance, created_smcs = self._cached_objects_for_filter[self.object_index].instantiate()
                for smc in created_smcs:
                    self.objects_by_filter["Edited"].append(smc)
                    self.objects_by_filter["All Objects"].append(smc)
                self.curr_obj = new_instance  # let's start editing this new object
                if self.curr_filter == "Prefab BP":
                    self.objects_by_filter["Prefab Instances"].append(new_instance)
        self.is_cache_dirty = True

    def delete_object(self) -> None:
        if self.curr_obj:
            if not self.curr_obj.b_dynamically_created and self.curr_obj not in self.deleted:
                self.deleted.append(self.curr_obj)
            super(InterctiveObjectHelper, self).delete_object()

    def copy(self) -> None:
        super().copy()

    def paste(self) -> None:
        self.clipboard: placeables.AbstractPlaceable
        if self.clipboard and not self.clipboard.is_destroyed:
            pasted, created = self.clipboard.instantiate()
            pasted.set_scale(self.clipboard.get_scale())
            pasted.set_rotation(self.clipboard.get_rotation())
            pasted.set_scale3d(self.clipboard.get_scale3d())
            pasted.set_materials(self.clipboard.get_materials())
            pasted.set_location(self.clipboard.get_location())
            self.objects_by_filter["Edited"].extend(created)
            self.objects_by_filter["All Objects"].extend(created)
            if not self.curr_obj:
                self.curr_obj = pasted
        self.is_cache_dirty = True

    def calculate_preview(self) -> None:
        super(InterctiveObjectHelper, self).calculate_preview()

    def post_render(self, pc: unrealsdk.UObject, offset: int) -> None:
        super().post_render(pc, offset)

        x, y, z = canvasutils.rot_to_vec3d([pc.CalcViewRotation.Pitch,
                                            pc.CalcViewRotation.Yaw,
                                            pc.CalcViewRotation.Roll])
        if settings.b_show_preview and self.curr_preview:
            _x, _y = canvasutils.euler_rotate_vector_2d(0, 1, pc.CalcViewRotation.Yaw)
            now = time()
            w = tan(radians(pc.ToHFOV(pc.GetFOVAngle()) / 2)) * 200
            _x *= (w - 80)
            _y *= (w - 80)
            self.curr_preview.set_preview_location((pc.Location.X + 200 * x - _x,
                                                    pc.Location.Y + 200 * y - _y,
                                                    pc.Location.Z + 200 * z))
            self.curr_preview.add_rotation((0,
                                            int((canvasutils.u_rotation_180 / 2.5) * (now - self.delta_time)),
                                            0))
            self.delta_time = now

        if self.curr_obj:
            self.curr_obj.draw_debug_box(pc)
            if not settings.b_lock_object_position:
                self.curr_obj.set_location(
                    (canvasutils.round_to_multiple(pc.Location.X + offset * x, settings.editor_grid_size),
                     canvasutils.round_to_multiple(pc.Location.Y + offset * y, settings.editor_grid_size),
                     canvasutils.round_to_multiple(pc.Location.Z + offset * z, settings.editor_grid_size)))
        else:
            # Now let us highlight the currently selected object (does not need to be the moved object!)
            if self._cached_objects_for_filter:
                self._cached_objects_for_filter[self.object_index].draw_debug_box(pc)

    def cleanup(self, mapname: str) -> None:
        super(InterctiveObjectHelper, self).cleanup(mapname)
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

        black_listed = [
            ("InteractiveObjectDefinition", "GD_Episode12Data.InteractiveObjects.InfoKiosk"),
            ("InteractiveObjectDefinition", "GD_Z2_TrailerTrashinData.InteractiveObjects.IO_MO_PropaneTanks"),
            ("InteractiveObjectBalanceDefinition", "GD_Z2_TrailerTrashinData.BalanceDefs.BD_PropaneTank")

        ]
        for _class, _object in black_listed:
            try:
                interactives.pop(interactives.index(unrealsdk.FindObject(_class, _object)))
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
                if placeable.holds_object(unrealsdk.FindObject("Object", to_destroy)):
                    self.deleted.append(placeable)
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
                    if iodef.holds_object(unrealsdk.FindObject("Object", obj)):
                        new_instance, _ = iodef.instantiate()
                        new_instance: placeables.InteractiveObjectBalanceDefinition

                        new_instance.set_location(attrs.get("Location", (0, 0, 0)))
                        new_instance.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                        new_instance.set_scale(attrs.get("Scale", 1))
                        new_instance.set_scale3d(attrs.get("Scale3D", (1, 1, 1)))

                        mats = attrs.get("Materials", None)
                        if mats is not None:
                            mats = [unrealsdk.FindObject("MaterialInstanceConstant", m) for m in mats]
                        new_instance.set_materials(mats)

                        self.objects_by_filter["Edited"].append(new_instance)
                        self.objects_by_filter["All Objects"].append(new_instance)
                        break

        for obj, attrs in map_data.get("Edit", {}).get("InteractiveObjectDefinition", {}).items():
            for placeable in self.objects_by_filter["All Objects"]:
                if placeable.holds_object(unrealsdk.FindObject("Object", obj)):
                    placeable: placeables.InteractiveObjectBalanceDefinition
                    placeable.set_location(attrs.get("Location", (0, 0, 0)))
                    placeable.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                    placeable.set_scale(attrs.get("Scale", 1))
                    placeable.set_scale3d(attrs.get("Scale3D", (1, 1, 1)))

                    mats = attrs.get("Materials", None)
                    if mats is not None:
                        mats = [unrealsdk.FindObject("MaterialInstanceConstant", m) for m in mats]
                    placeable.set_materials(mats)

                    self.objects_by_filter["Edited"].append(placeable)
                    break

    def save_map(self, map_data: dict) -> None:
        for placeable in self.objects_by_filter["All Objects"]:
            placeable.save_to_json(map_data)

        for deleted in self.deleted:
            deleted.save_to_json(map_data)
