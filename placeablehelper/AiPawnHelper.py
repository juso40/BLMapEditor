from time import time
from typing import List, Tuple

import unrealsdk
from unrealsdk import *

from .placeablehelper import PlaceableHelper
from .. import bl2tools
from .. import canvasutils
from .. import placeables
from .. import settings


class AiPawnHelper(PlaceableHelper):

    def __init__(self):
        super().__init__(name="Edit AiPawns",
                         supported_filters=["Create", "Edited"])

    def on_enable(self) -> None:
        super(AiPawnHelper, self).on_enable()

    def on_disable(self) -> None:
        super(AiPawnHelper, self).on_disable()

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

    def get_filter(self) -> str:
        return super().get_filter()

    def get_index_of_total(self) -> str:
        return super().get_index_of_total()

    def change_filter(self) -> None:
        super().change_filter()

    def index_up(self) -> Tuple[str, List[placeables.AbstractPlaceable], int]:
        return super().index_up()

    def index_down(self) -> Tuple[str, List[placeables.AbstractPlaceable], int]:
        return super().index_down()

    def add_rotation(self, rotator: tuple) -> None:
        super(AiPawnHelper, self).add_rotation(rotator)

    def add_scale(self, scale: float) -> None:
        super(AiPawnHelper, self).add_scale(scale)

    def tp_to_selected_object(self, pc: unrealsdk.UObject) -> bool:
        if self.curr_filter == "Create":
            return False
        else:
            pc.Location = tuple(self.objects_by_filter[self.curr_filter][self.object_index].get_location())
            return True

    def restore_objects_defaults(self) -> None:
        bl2tools.feedback("Reset", "Cannot Reset custom AiPawn!", 4)
        return

    def move_object(self, b_move: bool) -> None:

        if self.curr_filter != "Create":
            self.curr_obj = self.objects_by_filter[self.curr_filter][self.object_index]

            if b_move:
                if self.curr_obj not in self.objects_by_filter["Edited"]:
                    self.objects_by_filter["Edited"].append(self.curr_obj)

        elif self.curr_filter == "Create" and b_move:
            # create a new instance from our Blueprint object
            new_instance, created = self.objects_by_filter[self.curr_filter][self.object_index].instantiate()
            self.objects_by_filter["Edited"].extend(created)
            self.curr_obj = new_instance  # let's start editing this new object

        if not b_move:
            self.curr_obj = None

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
            pasted.set_location(self.clipboard.get_location())
            self.objects_by_filter["Edited"].extend(created)
            if not self.curr_obj:
                self.curr_obj = pasted

    def calculate_preview(self) -> None:
        super(AiPawnHelper, self).calculate_preview()

    def post_render(self, canvas: unrealsdk.UObject, pc: unrealsdk.UObject, offset: int, b_pos_locked: bool) -> None:
        if settings.b_show_preview and self.curr_preview:
            x, y, z = canvasutils.rot_to_vec3d([pc.CalcViewRotation.Pitch + canvasutils.u_rotation_180 // 8,
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
                self.curr_obj.set_location(
                    (canvasutils.round_to_multiple(pc.Location.X + offset * x, settings.editor_grid_size),
                     canvasutils.round_to_multiple(pc.Location.Y + offset * y, settings.editor_grid_size),
                     canvasutils.round_to_multiple(pc.Location.Z + offset * z, settings.editor_grid_size)))
        else:
            # Now let us highlight the currently selected object (does not need to be the moved object!)
            if not self.objects_by_filter[self.curr_filter]:
                self.change_filter()
            self.objects_by_filter[self.curr_filter][self.object_index].draw_debug_box(pc)
            self.objects_by_filter[self.curr_filter][self.object_index].draw_debug_origin(canvas, pc)

    def cleanup(self, mapname: str) -> None:
        super(AiPawnHelper, self).cleanup(mapname)

    def setup(self, mapname: str) -> None:
        if mapname == "menumap" or mapname == "none" or mapname == "":
            return

        self.objects_by_filter["Create"].extend([
            placeables.AIPawnBalanceDefinition(x.PlayThroughs[0].DisplayName if x.PlayThroughs[0].DisplayName else
                                               bl2tools.get_obj_path_name(x).split(".")[-1], x)
            for x in unrealsdk.FindAll("AIPawnBalanceDefinition")[1:]]
        )

        self.objects_by_filter["Create"].sort(key=lambda obj: obj.name)

    def load_map(self, map_data: dict) -> None:

        for bp in map_data.get("Create", {}).get("AIPawnBalanceDefinition", []):
            for obj, attrs in bp.items():
                for pawn_bp in self.objects_by_filter["Create"]:  # type: placeables.AbstractPlaceable
                    if pawn_bp.holds_object(obj):
                        new_instance, _ = pawn_bp.instantiate()
                        new_instance.set_location(attrs.get("Location", (0, 0, 0)))
                        new_instance.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                        new_instance.set_scale(attrs.get("Scale", 1))
                        self.objects_by_filter["Edited"].append(new_instance)
                        break

    def save_map(self, map_data: dict) -> None:
        for placeable in self.objects_by_filter["Edited"]:
            placeable.save_to_json(map_data)
