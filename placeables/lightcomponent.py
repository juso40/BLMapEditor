from typing import Tuple, List, Union

import unrealsdk
from unrealsdk import *

from .placeable import AbstractPlaceable

from .. import canvasutils
from .. import bl2tools
from .. import settings


"""
Do not use!
Still need to figure out how to instantiate a new light source.
"""


class LightComponent(AbstractPlaceable):
    def __init__(self, name: str, light_class: str, light_component: unrealsdk.UObject = None):
        super().__init__(name, "LightComponent")
        self.light_class: str = light_class
        self.light_component: unrealsdk.UObject = light_component
        self.light_component_name: str = ""  # ...but we may still need its name for saving it later to json

    def get_materials(self) -> List[unrealsdk.UObject]:
        return []

    def set_materials(self, materials: List[unrealsdk.UObject]) -> None:
        return

    def add_material(self, material: unrealsdk.UObject) -> None:
        return

    def remove_material(self, material: unrealsdk.UObject = None, index: int = -1) -> None:
        return

    def set_scale(self, scale: float) -> None:
        return

    def get_scale(self) -> float:
        return 1

    def add_scale(self, scale: float) -> None:
        return

    def get_scale3d(self) -> List[float]:
        return [1, 1, 1]

    def set_scale3d(self, scale3d: List[float]) -> None:
        return

    def set_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        if self.light_component and self.light_component.Rotation:
            self.light_component.Rotation.Pitch = rotator[0]
            self.light_component.Rotation.Yaw = rotator[1]
            self.light_component.Rotation.Roll = rotator[2]
            self.light_component.ForceUpdate(False)
            self.b_default_attributes = False

    def get_rotation(self) -> List[int]:
        if self.light_component and self.light_component.Rotation:
            return [self.light_component.Rotation.Pitch,
                    self.light_component.Rotation.Yaw,
                    self.light_component.Rotation.Roll]
        return [0, 0, 0]

    def add_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        if self.light_component and self.light_component.Rotation:
            pitch, yaw, roll = rotator
            self.light_component.Rotation.Pitch += pitch
            self.light_component.Rotation.Yaw += yaw
            self.light_component.Rotation.Roll += roll
            self.light_component.ForceUpdate(False)
            self.b_default_attributes = False

    def set_location(self, position: Union[List[float], Tuple[float, float, float]]) -> None:
        if not self.light_component:
            return
        x, y, z = position
        self.light_component.CachedParentToWorld.WPlane.X = x
        self.light_component.CachedParentToWorld.WPlane.Y = y
        self.light_component.CachedParentToWorld.WPlane.Z = z
        self.light_component.ForceUpdate(False)
        self.b_default_attributes = False

    def get_location(self) -> List[float]:
        if not self.light_component:
            return [0, 0, 0]
        return [self.light_component.CachedParentToWorld.WPlane.X,
                self.light_component.CachedParentToWorld.WPlane.Y,
                self.light_component.CachedParentToWorld.WPlane.Z]

    def draw_debug_box(self, player_controller: unrealsdk.UObject) -> None:
        if self.light_component:
            player_controller.DrawDebugBox(
                (self.light_component.CachedParentToWorld.WPlane.X,
                 self.light_component.CachedParentToWorld.WPlane.Y,
                 self.light_component.CachedParentToWorld.WPlane.Z),
                (50,
                 50,
                 50),
                *settings.draw_debug_box_color, True, 0.01
            )

    def draw_debug_origin(self, canvas: unrealsdk.UObject, player_controller: unrealsdk.UObject) -> None:
        return
        if self.light_component:
            screen_x, screen_y = canvasutils.world_to_screen(
                canvas, self.get_location(),
                [player_controller.CalcViewRotation.Pitch,
                 player_controller.CalcViewRotation.Yaw,
                 player_controller.CalcViewRotation.Roll],
                [player_controller.Location.X,
                 player_controller.Location.Y,
                 player_controller.Location.Z],
                player_controller.ToHFOV(player_controller.GetFOVAngle())
            )
            canvasutils.draw_box(canvas, 5, 5, screen_x - 5, screen_y - 5, settings.draw_debug_origin_color)

    def instantiate(self) -> Tuple[AbstractPlaceable, List[AbstractPlaceable]]:
        pc = bl2tools.get_player_controller()
        _loc = (pc.Location.X, pc.Location.Y, pc.Location.Z)
        collection_actor = unrealsdk.FindAll("StaticLightCollectionActor")[-1]
        light_component = unrealsdk.ConstructObject(Class=self.light_class, Outer=collection_actor)
        unrealsdk.Log(light_component)
        ret = LightComponent(self.name, self.light_class, light_component)
        collection_actor.AttachComponent(light_component)
        collection_actor.MaxLightComponents += 1

        ret.b_dynamically_created = True

        return ret, [ret, ]

    def get_preview(self) -> AbstractPlaceable:
        ret, _ = self.instantiate()
        return ret

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unrealsdk.UObject) -> bool:
        return self.light_component is uobject

    def destroy(self) -> List[AbstractPlaceable]:
        if self.light_component is None:
            raise ValueError("Cannot destroy not instantiated Object!")
        # the light_actor may get GC'ed, but we need its name to save it later
        if not self.b_dynamically_created:
            self.light_component_name = bl2tools.get_obj_path_name(self.light_component)
        self.set_location((-99999, -99999, -99999))
        self.light_component.DetachFromAny()
        self.is_destroyed = True
        return [self, ]

    def store_default_values(self, default_dict: dict) -> None:
        if self.light_component and bl2tools.get_obj_path_name(self.light_component) not in default_dict:
            default_dict[bl2tools.get_obj_path_name(self.light_component)] = {
                "Location": self.get_location(),
                "Rotation": self.get_rotation(),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials":
                    [bl2tools.get_obj_path_name(x)
                     for x in self.get_materials()]
            }

    def restore_default_values(self, default_dict: dict) -> None:
        if self.light_component and bl2tools.get_obj_path_name(self.light_component) in default_dict:
            defaults = default_dict[bl2tools.get_obj_path_name(self.light_component)]
            self.set_scale(defaults["Scale"])
            self.set_location(defaults["Location"])
            self.set_rotation(defaults["Rotation"])
            self.set_scale3d(defaults["Scale3D"])
            self.set_materials(defaults["Materials"])
            self.b_default_attributes = True

    def save_to_json(self, saved_json: dict) -> None:
        if not self.b_dynamically_created and self.b_default_attributes and not self.is_destroyed:
            return
        elif not self.b_dynamically_created and not self.b_default_attributes and not self.is_destroyed:
            smc_list = saved_json.setdefault("Edit", {}).setdefault("Light", {})
            smc_list[bl2tools.get_obj_path_name(self.light_component)] = {"Location": self.get_location(),
                                                                          "Rotation": self.get_rotation(),
                                                                          "Scale": self.get_scale(),
                                                                          "Scale3D": self.get_scale3d(),
                                                                          "Materials":
                                                                              [bl2tools.get_obj_path_name(x)
                                                                               for x in self.get_materials()]
                                                                          }

        elif not self.b_dynamically_created and self.is_destroyed:
            smc_list = saved_json.setdefault("Destroy", {}).setdefault("Light", [])
            smc_list.append(self.light_component)

        elif self.b_dynamically_created:
            lights_list = saved_json.setdefault("Create", {}).setdefault("Light", [])
            lights_list.append(
                {bl2tools.get_obj_path_name(self.light_class): {"Location": self.get_location(),
                                                                "Rotation": self.get_rotation(),
                                                                "Scale": self.get_scale(),
                                                                "Scale3D": self.get_scale3d(),
                                                                "Materials":
                                                                    [bl2tools.get_obj_path_name(x)
                                                                     for x in self.get_materials()]
                                                                }}
            )

    def draw(self) -> None:
        super().draw()
