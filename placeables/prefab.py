import collections
import json
import os
import pathlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

import unrealsdk  # type: ignore

from Mods.uemath import Rotator, Vector

from .interactiveobject import InteractiveObjectBalanceDefinition
from .pawn import AIPawnBalanceDefinition
from .placeable import AbstractPlaceable
from .staticmesh import StaticMeshComponent


class Prefab(AbstractPlaceable):
    @dataclass()
    class ComponentData:
        data: AbstractPlaceable
        offset: list
        rotation: list
        scale: float
        scale3d: list
        move_offset: list  # needs to be recalculated after rotation and scale

    def __init__(self, name: str) -> None:
        super().__init__(name, "Prefab")
        self.component_data: List[Prefab.ComponentData] = []
        self._location: list = [0, 0, 0]
        self._rotation: list = [0, 0, 0]
        self._scale: float = 1.0
        self._scale3d: list = [1.0, 1.0, 1.0]

    @staticmethod
    def create_prefab_blueprint(placeables: List[AbstractPlaceable], name: str) -> "Prefab":
        """
        Create a Prefab Blueprint from existing AbstractPlaceable in the map.
        :param name:
        :param placeables: List of Instantiated Placeables.
        :return: Returns a Prefab Blueprint
        """
        blueprint = Prefab(name)
        for placeable in placeables:
            # Component Data holds the initial 'Blueprint' data of this Prefab
            blueprint.component_data.append(
                Prefab.ComponentData(
                    data=placeable,  # The Placeable itself
                    offset=[0, 0, 0],  # This will be calculated later
                    rotation=placeable.get_rotation(),  # The initial rotation
                    scale=placeable.get_scale(),  # The initial scale
                    scale3d=placeable.get_scale3d(),  # The initial scale3d
                    move_offset=[0, 0, 0],  # The offset after rotation and scale
                ),
            )
        # After we have all the data, we need to calculate the offsets
        blueprint._calculate_offsets()
        blueprint._write_prefab_json()  # Write the blueprint to a json file
        return blueprint

    @staticmethod
    def load_prefab_json(name: str) -> Optional["Prefab"]:
        """
        Loads one single prefab from existing prefab_*.json file.
        :param name:
        :return:
        """
        path = pathlib.Path(__file__).parent.parent / "Prefabs" / f"prefab_{name}.json"
        if not os.path.isfile(path):
            unrealsdk.Log(f"No prefab with the name {name} exists!")
            return None

        blueprint = Prefab(name)
        with open(path) as fp:
            bp = json.load(fp)
        for part in bp:
            for uobj_name, attrs in part.items():
                uobj = unrealsdk.FindObject("Object", uobj_name)
                if uobj is None:
                    continue
                if uobj.Class.Name == "StaticMesh":
                    new = StaticMeshComponent(uobj_name.split(".", 1)[-1], uobj)
                elif uobj.Class.Name in (
                    "WillowInteractiveObject",
                    "WillowVendingMachine",
                    "WillowVendingMachineBlackMarket",
                    "InteractiveObjectBalanceDefinition",
                    "InteractiveObjectDefinition",
                ):
                    new = InteractiveObjectBalanceDefinition(uobj_name.split(".", 1)[-1], uobj)
                elif uobj.Class.Name == "AIPawnBalanceDefinition":
                    new = AIPawnBalanceDefinition(uobj_name.split(".", 1)[-1], uobj)
                else:
                    continue
                blueprint.component_data.append(
                    Prefab.ComponentData(
                        data=new,
                        offset=attrs["Offset"],
                        rotation=attrs["Rotation"],
                        scale=attrs["Scale"],
                        scale3d=attrs["Scale3D"],
                        move_offset=attrs.get("MoveOffset", [0, 0, 0]),
                    ),
                )
        return blueprint

    def _write_prefab_json(self) -> None:
        """
        Writes this prefabs data to a prefab_*.json file.
        :return:
        """
        with open(pathlib.Path(__file__).parent.parent / "Prefabs" / f"prefab_{self.name}.json", "w") as fp:
            prefab_data = [
                {
                    x.data.uobject_path_name: {
                        "Offset": x.offset,
                        "Rotation": x.rotation,
                        "Scale": x.scale,
                        "Scale3D": x.scale3d,
                        "MoveOffset": x.move_offset,
                    },
                }
                for x in self.component_data
            ]
            json.dump(prefab_data, fp)

    def _calculate_offsets(self) -> None:
        """Calculate the initial offsets of all components, relative to the root component."""
        if not self.component_data:
            return
        self._location = self.component_data[0].data.get_location()  # update our root location
        root = Vector(self._location)
        # Make sure our object has normal rotation and scale for this calculation
        self._rotation = [0, 0, 0]
        self._scale = 1.0
        self._scale3d = [1.0, 1.0, 1.0]
        for component in self.component_data:
            offset = Vector(component.data.get_location()) - root
            component.offset = list(offset.to_tuple())  # This is the initial offset of this child component
            # without rotation or scale our move offset is the same as the initial offset
            component.move_offset = component.offset.copy()

    def _calculate_move_offsets(self) -> None:
        """Update the move offsets of all components after rotation and scale changes."""
        f, r, u = Rotator(self._rotation).get_axes()
        scale_x, scale_y, scale_z = self._scale3d
        for component in self.component_data:
            offset = Vector(component.offset)
            component.move_offset = list(
                (self._scale * (offset.x * f * scale_x + offset.y * r * scale_y + offset.z * u * scale_z)).to_tuple(),
            )

    def instantiate(self) -> Tuple["Prefab", List[AbstractPlaceable]]:
        """Place the prefab saved by this instance."""
        ret = Prefab(self.name)  # we only want to return the instantiated Prefab from our own BP
        new_components = []
        for component in self.component_data:
            main_obj, new = component.data.instantiate()  # Instantiate our child objects
            # Set our child objects correct scale and rotation
            main_obj.set_scale(component.scale)
            main_obj.set_scale3d(component.scale3d)
            main_obj.set_rotation(component.rotation)

            new_components.extend(new)
            ret.component_data.append(
                Prefab.ComponentData(  # We can just copy the data from our own BP
                    main_obj,  # only update the child object data
                    component.offset.copy(),
                    component.rotation.copy(),
                    component.scale,
                    component.scale3d.copy(),
                    component.move_offset.copy(),
                ),
            )
        ret.set_location(self.get_location())
        return ret, new_components

    def get_preview(self) -> AbstractPlaceable:
        ret, _ = self.instantiate()
        ret: Prefab = ret
        _, box_extent = ret.get_bounding_box()
        size = max(box_extent)
        ret.set_scale(1 / size * 20)
        return ret

    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unrealsdk.UObject) -> bool:
        if not self.component_data:
            return False
        return any(x.data.holds_object(uobject) for x in self.component_data)

    def set_scale(self, scale: float) -> None:
        self._scale = scale if scale != 0 else self._scale
        for component in self.component_data:
            new_scale = component.scale * self._scale  # Scale the initial scaling of our child
            component.data.set_scale(new_scale)
        self._calculate_move_offsets()  # update move offsets after scale change

    def get_scale(self) -> float:
        return self._scale

    def add_scale(self, scale: float) -> None:
        self.set_scale(self._scale + scale)

    def set_rotation(self, rotator: Iterable) -> None:
        self.add_rotation((Rotator(rotator) - Rotator(self._rotation)).to_tuple())

    def get_rotation(self) -> Iterable:
        return self._rotation.copy()

    def set_location(self, position: Union[List[float], Tuple[float, float, float]]) -> None:
        self._location = list(position)
        for component in self.component_data:
            component.data.set_location((Vector(component.move_offset) + Vector(position)).to_tuple())

    def destroy(self) -> List[AbstractPlaceable]:
        remove: List[AbstractPlaceable] = [
            self,
        ]
        for component in self.component_data:
            remove.extend(component.data.destroy())

        self.is_destroyed = True
        return remove

    def get_bounding_box(self) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        box_origin = Vector(self._location)
        box_extent = Vector()
        for component in self.component_data:
            child_origin, child_extent = component.data.get_bounding_box()
            child_origin = Vector(child_origin)
            child_extent = Vector(child_extent)
            box_origin.x = min(box_origin.x, child_origin.x)
            box_origin.y = min(box_origin.y, child_origin.y)
            box_origin.z = min(box_origin.z, child_origin.z)
            box_extent.x = max(box_extent.x, child_extent.x)
            box_extent.y = max(box_extent.y, child_extent.y)
            box_extent.z = max(box_extent.z, child_extent.z)
        return box_origin.to_tuple(), box_extent.to_tuple()

    def get_location(self) -> List[float]:
        return self._location

    def add_rotation(self, rotator: Tuple[int, int, int]) -> None:
        """Rotate the whole prefab by the given rotator.
        Root object rotates around its own origin, all other objects rotate and move around the root object's origin.
        """

        rotation = Rotator(rotator)  # global rotation Auf Komplett Prefab
        root_rot = Rotator(self._rotation)
        self._rotation = list((root_rot + rotation).to_tuple())
        root_rot = Rotator(self._rotation)
        self._calculate_move_offsets()  # update move offsets after rotation change
        f, r, u = root_rot.get_axes()
        for component in self.component_data:
            child = component.data
            child_rotator = Rotator(child.get_rotation())
            child_rotator.yaw += rotation.yaw
            cf, cr, cu = child_rotator.get_axes()
            child_rotator.pitch += r.dot(cf) * rotation.roll
            child_rotator.roll += f.dot(cf) * rotation.roll
            child.set_rotation(child_rotator.to_tuple())

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

    def get_materials(self) -> List[unrealsdk.UObject]:
        return []

    def set_materials(self, materials: List[unrealsdk.UObject]) -> None:
        pass

    def add_material(self, material: unrealsdk.UObject) -> None:
        super().add_material(material)

    def remove_material(self, material: unrealsdk.UObject = None, index: int = -1) -> None:
        super().remove_material(material, index)

    def get_scale3d(self) -> List[float]:
        return self._scale3d.copy()

    def set_scale3d(self, scale3d: List[float]) -> None:
        self._scale3d = [scale if scale != 0 else old_scale for scale, old_scale in zip(scale3d, self._scale3d)]
        s_x, s_y, s_z = self._scale3d
        for component in self.component_data:
            child = component.data
            c_x, c_y, c_z = component.scale3d  # we need to scale the child by the components initial scale
            child.set_scale3d([c_x * s_x, c_y * s_y, c_z * s_z])
        self._calculate_move_offsets()
