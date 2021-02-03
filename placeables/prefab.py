from __future__ import annotations
from typing import List, Tuple, Union
from dataclasses import dataclass

import json
import os
import math

import unrealsdk
from unrealsdk import *

from .placeable import AbstractPlaceable
from .staticmesh import StaticMeshComponent

from .. import bl2tools


class Prefab(AbstractPlaceable):
    @dataclass()
    class ComponentData:
        data: AbstractPlaceable
        offset: list
        rotation: list
        scale: float

    def __init__(self, name: str):
        super().__init__(name, "Prefab")
        self.component_data: List[Prefab.ComponentData] = []

    @staticmethod
    def create_prefab_from_smc(static_mesh_components: List[AbstractPlaceable], name: str) -> Prefab:
        """
        Create a Prefab Blueprint from existing AbstractPlaceable in the map.
        :param name:
        :param static_mesh_components: List of StaticMeshComponents
        :return: Returns a Prefab Blueprint
        """
        blueprint = Prefab(name)
        for smc in static_mesh_components:
            # add all the existing AbstractPlaceables to calculate initial offset
            blueprint.component_data.append(Prefab.ComponentData(smc, [0, 0, 0], smc.get_rotation(), smc.get_scale()))
        blueprint._calculate_offsets()
        offsets = [x.offset for x in blueprint.component_data]
        # ugly but it works
        blueprint.component_data.clear()  # then delete the existing AbstractPlaceables
        for smc, offset in zip(static_mesh_components, offsets):
            # and fill this BP with BP version of them
            blueprint.component_data.append(Prefab.ComponentData(StaticMeshComponent(smc.name, smc.static_mesh),
                                                                 offset, smc.get_rotation(), smc.get_scale()))

        blueprint._write_prefab_json()

        return blueprint

    @staticmethod
    def load_prefab_json(name) -> Union[Prefab, None]:
        """
        Loads one single prefab from existing prefab_*.json file.
        :param name:
        :return:
        """
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "Prefabs", f"prefab_{name}.json")
        if not os.path.isfile(path):
            unrealsdk.Log(f"No prefab with the name {name} exists!")
            return None

        blueprint = Prefab(name)
        with open(path) as fp:
            bp = json.load(fp)
        for part in bp:
            for mesh, attrs in part.items():
                new = StaticMeshComponent(mesh.split(".", 1)[-1], unrealsdk.FindObject("StaticMesh", mesh))
                blueprint.component_data.append(Prefab.ComponentData(new, attrs["Offset"],
                                                                     attrs["Rotation"], attrs["Scale"]))
        return blueprint

    def _write_prefab_json(self) -> None:
        """
        Writes this prefabs data to a prefab_*.json file.
        :param path:
        :return:
        """
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..",
                               "Prefabs", f"prefab_{self.name}.json"), "w") as fp:
            save_this = [{bl2tools.get_obj_path_name(x.data.static_mesh): {"Offset": x.offset,
                                                                           "Rotation": x.rotation,
                                                                           "Scale": x.scale}
                          } for x in self.component_data]
            json.dump(save_this, fp)

    def _calculate_offsets(self) -> None:
        """
        Calculate all offsets depending on the MeshData in index 0.
        :return:
        """
        base = self.component_data[0]  # type: Prefab.ComponentData
        base.offset = [0, 0, 0]  # reset the base offset
        base_loc = base.data.get_location()
        for child in self.component_data[1:]:  # type: Prefab.ComponentData
            x, y, z = child.data.get_location()
            d_x = x - base_loc[0]
            d_y = y - base_loc[1]
            d_z = z - base_loc[2]
            child.offset = [d_x, d_y, d_z]

    def instantiate(self) -> Tuple[AbstractPlaceable, List[AbstractPlaceable]]:
        """
        Place the prefab saved by this instance.
        :param location:
        :return:
        """
        ret = Prefab(self.name)  # we only want to return the instantiated Prefab from our own BP

        new_components = []
        for component in self.component_data:
            smc, new = component.data.instantiate()
            smc.set_scale(component.scale)
            smc.set_rotation(component.rotation)
            new_components.extend(new)
            ret.component_data.append(Prefab.ComponentData(smc,
                                                           component.offset.copy(),
                                                           component.rotation.copy(),
                                                           component.scale
                                                           )
                                      )
        return ret, new_components

    def get_preview(self) -> AbstractPlaceable:
        return None

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        return None

    def holds_object(self, uobject: str) -> bool:
        if not self.component_data:
            return False
        return any(x.data.holds_object(uobject) for x in self.component_data)

    def set_scale(self, scale: float) -> None:
        return

    def get_scale(self) -> float:
        return 0

    def add_scale(self, scale: float) -> None:
        for component in self.component_data:
            component.data.add_scale(scale)

    def set_rotation(self, rotator: iter) -> None:
        return

    def get_rotation(self) -> iter:
        return [0, 0, 0]

    def set_location(self, location):
        for smc in self.component_data:  # type: Prefab.ComponentData
            smc.data.set_location(
                [location[0] + smc.offset[0], location[1] + smc.offset[1], location[2] + smc.offset[2]])

    def destroy(self) -> List[AbstractPlaceable]:
        remove = [self, ]
        for component in self.component_data:
            remove.extend(component.data.destroy())

        self.is_destroyed = True
        return remove

    def draw_debug_box(self, player_controller) -> None:
        for component in self.component_data:
            component.data.draw_debug_box(player_controller)

    def draw_debug_origin(self, canvas, player_controller) -> None:
        if not self.component_data[0].data:
            return
        self.component_data[0].data.draw_debug_origin(canvas, player_controller)

    def get_location(self) -> iter:
        return self.component_data[0].data.get_location()

    def add_rotation(self, rotator: iter) -> None:
        pitch, yaw, roll = rotator
        cosa = math.cos(yaw)
        sina = math.sin(yaw)

        cosb = math.cos(pitch)
        sinb = math.sin(pitch)

        cosc = math.cos(roll)
        sinc = math.sin(roll)

        Axx = cosa * cosb
        Axy = cosa * sinb * sinc - sina * cosc
        Axz = cosa * sinb * cosc + sina * sinc
        Ayx = sina * cosb
        Ayy = sina * sinb * sinc + cosa * cosc
        Ayz = sina * sinb * cosc - cosa * sinc
        Azx = -sinb
        Azy = cosb * sinc
        Azz = cosb * cosc

        for point in self.component_data:  # type: Prefab.ComponentData
            px, py, pz = point.data.get_location()

            point.data.set_location([Axx * px + Axy * py + Axz * pz,
                                     Ayx * px + Ayy * py + Ayz * pz,
                                     Azx * px + Azy * py + Azz * pz])

        self._calculate_offsets()

    def store_default_values(self, default_dict: dict) -> None:
        if not self.component_data:
            return

        for component in self.component_data:
            component.data.store_default_values(default_dict)

    def restore_default_values(self, default_dict: dict) -> None:
        if not self.component_data:
            return
        for component in self.component_data:
            component.data.restore_default_values(default_dict)

    def save_to_json(self, saved_json: dict) -> None:
        pass
