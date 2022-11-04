from time import time
from typing import List, Tuple, Dict, cast
from math import tan, radians

import unrealsdk
from unrealsdk import *

from .placeablehelper import PlaceableHelper
from .. import bl2tools
from .. import canvasutils
from .. import placeables
from .. import settings


class AiPawnHelper(PlaceableHelper):

    def __init__(self):
        super().__init__(name="Edit AiPawns", supported_filters=["Create", "Edited"])

    def on_enable(self) -> None:
        super(AiPawnHelper, self).on_enable()

    def on_disable(self) -> None:
        super(AiPawnHelper, self).on_disable()

    def add_to_prefab(self) -> None:
        pass

    def get_filter(self) -> str:
        return super().get_filter()

    def get_index_of_total(self) -> str:
        return super().get_index_of_total()

    def add_rotation(self, rotator: tuple) -> None:
        super(AiPawnHelper, self).add_rotation(rotator)

    def add_scale(self, scale: float) -> None:
        super(AiPawnHelper, self).add_scale(scale)

    def tp_to_selected_object(self, pc: unrealsdk.UObject) -> bool:
        if self.curr_filter == "Create":
            return False
        else:
            pc.Location = tuple(self._cached_objects_for_filter[self.object_index].get_location())
            return True

    def restore_objects_defaults(self) -> None:
        return

    def move_object(self) -> None:
        if self.curr_obj:
            self.curr_obj = None
        else:
            if self.curr_filter != "Create":
                self.curr_obj = self._cached_objects_for_filter[self.object_index]
                if self.curr_obj not in self.objects_by_filter["Edited"]:
                    self.objects_by_filter["Edited"].append(self.curr_obj)

            elif self.curr_filter == "Create":
                # create a new instance from our Blueprint object
                new_instance, created = self._cached_objects_for_filter[self.object_index].instantiate()
                self.objects_by_filter["Edited"].extend(created)
                self.curr_obj = new_instance  # let's start editing this new object
        self.is_cache_dirty = True

    def delete_object(self) -> None:
        if self.curr_obj:
            super(AiPawnHelper, self).delete_object()

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
            if not self.curr_obj:
                self.curr_obj = pasted
        self.is_cache_dirty = True

    def calculate_preview(self) -> None:
        super(AiPawnHelper, self).calculate_preview()

    def post_render(self, pc: unrealsdk.UObject, offset: int) -> None:
        super().post_render(pc, offset)
        x, y, z = canvasutils.rot_to_vec3d(
            [pc.CalcViewRotation.Pitch,
             pc.CalcViewRotation.Yaw,
             pc.CalcViewRotation.Roll]
            )
        if settings.b_show_preview and self.curr_preview:
            _x, _y = canvasutils.euler_rotate_vector_2d(0, 1, pc.CalcViewRotation.Yaw)
            now = time()
            w = tan(radians(pc.ToHFOV(pc.GetFOVAngle()) / 2)) * 200
            _x *= (w - 80)
            _y *= (w - 80)
            self.curr_preview.set_preview_location(
                (pc.Location.X + 200 * x - _x,
                 pc.Location.Y + 200 * y - _y,
                 pc.Location.Z + 200 * z)
                )
            self.curr_preview.add_rotation(
                (0,
                 int((canvasutils.u_rotation_180 / 2.5) * (now - self.delta_time)),
                 0)
                )
            self.delta_time = now

        if self.curr_obj:
            self.curr_obj.draw_debug_box(pc)
            if not settings.b_lock_object_position:
                self.curr_obj.set_location(
                    (canvasutils.round_to_multiple(pc.Location.X + offset * x, settings.editor_grid_size),
                     canvasutils.round_to_multiple(pc.Location.Y + offset * y, settings.editor_grid_size),
                     canvasutils.round_to_multiple(pc.Location.Z + offset * z, settings.editor_grid_size))
                )
        else:
            # Now let us highlight the currently selected object (does not need to be the moved object!)
            if self._cached_objects_for_filter:
                self._cached_objects_for_filter[self.object_index].draw_debug_box(pc)

    def cleanup(self, mapname: str) -> None:
        super(AiPawnHelper, self).cleanup(mapname)

    def setup(self, mapname: str) -> None:
        if mapname == "menumap" or mapname == "none" or mapname == "":
            return

        self.objects_by_filter["Create"].extend(
            [
                placeables.AIPawnBalanceDefinition(
                    x.PlayThroughs[0].DisplayName if x.PlayThroughs[0].DisplayName else
                    bl2tools.get_obj_path_name(x).split(".")[-1], x
                    )
                for x in unrealsdk.FindAll("AIPawnBalanceDefinition")[1:]]
        )

        self.objects_by_filter["Create"].sort(key=lambda obj: obj.name)

    def load_map(self, map_data: dict) -> None:

        for bp in map_data.get("Create", {}).get("AIPawnBalanceDefinition", []):
            for obj, attrs in bp.items():
                for pawn_bp in self.objects_by_filter["Create"]:  # type: placeables.AbstractPlaceable
                    if pawn_bp.holds_object(unrealsdk.FindObject("AIPawnBalanceDefinition", obj)):
                        new_instance, _ = pawn_bp.instantiate()
                        new_instance: placeables.AIPawnBalanceDefinition

                        new_instance.set_location(attrs.get("Location", (0, 0, 0)))
                        new_instance.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                        new_instance.set_scale(attrs.get("Scale", 1))
                        new_instance.set_scale3d(attrs.get("Scale3D", (1, 1, 1)))

                        mats = attrs.get("Materials", None)
                        if mats is not None:
                            mats = [unrealsdk.FindObject("MaterialInstanceConstant", m) for m in mats]
                        new_instance.set_materials(mats)

                        self.objects_by_filter["Edited"].append(new_instance)
                        break

    def save_map(self, map_data: dict) -> None:
        for placeable in self.objects_by_filter["Edited"]:
            placeable.save_to_json(map_data)
