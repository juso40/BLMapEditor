from __future__ import annotations

import json
import os
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from uemath import Rotator, Vector
from unrealsdk import find_object, make_struct, unreal

from .interactiveobject import InteractiveObjectPlaceable
from .pawn import AIPawnPlaceable
from .placeable import AbstractPlaceable
from .staticmesh import StaticMeshComponentPlaceable

if TYPE_CHECKING:
    from common import AIPawnBalanceDefinition, InteractiveObjectDefinition, MaterialInterface, Object, StaticMesh

    make_vector = Object.Vector.make_struct
else:
    make_vector = make_struct


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
        self.component_data: list[Prefab.ComponentData] = []
        self._location: list[float] = [0, 0, 0]
        self._rotation: list[int] = [0, 0, 0]
        self._scale: float = 1.0
        self._scale3d: list = [1.0, 1.0, 1.0]

    @staticmethod
    def create_prefab_blueprint(placeables: list[AbstractPlaceable], name: str) -> Prefab:
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
    def load_prefab_json(name: str) -> Prefab | None:
        """
        Loads one single prefab from existing prefab_*.json file.
        :param name:
        :return:
        """
        path = pathlib.Path(__file__).parent.parent / "Prefabs" / f"prefab_{name}.json"
        if not os.path.isfile(path):
            print(f"No prefab with the name {name} exists!")
            return None

        blueprint = Prefab(name)
        with open(path) as fp:
            bp = json.load(fp)
        for part in bp:
            for uobj_name, attrs in part.items():
                uobj = find_object("Object", uobj_name)
                if uobj is None:
                    continue
                if uobj.Class.Name == "StaticMesh":
                    new = StaticMeshComponentPlaceable(uobj_name.split(".", 1)[-1], cast("StaticMesh", uobj))
                elif uobj.Class.Name in (
                    "WillowInteractiveObject",
                    "WillowVendingMachine",
                    "WillowVendingMachineBlackMarket",
                    "InteractiveObjectBalanceDefinition",
                    "InteractiveObjectDefinition",
                ):
                    new = InteractiveObjectPlaceable(
                        uobj_name.split(".", 1)[-1],
                        cast("InteractiveObjectDefinition", uobj),
                    )
                elif uobj.Class.Name == "AIPawnBalanceDefinition":
                    new = AIPawnPlaceable(uobj_name.split(".", 1)[-1], cast("AIPawnBalanceDefinition", uobj))
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

    def _apply_child_world_transform(self) -> None:
        """Recompute and apply world position/rotation for all children from parent state + stored local data."""
        parent_pos = Vector(self._location)
        parent_rot = Rotator(self._rotation)
        s_x, s_y, s_z = self._scale3d

        for component in self.component_data:
            local_offset = Vector(component.offset)
            rotated = local_offset.rotate_around(Vector(), Rotator(self._rotation))
            component.move_offset = list(
                (self._scale * Vector(x=rotated.x * s_x, y=rotated.y * s_y, z=rotated.z * s_z)).to_tuple(),
            )
            component.data.set_location((parent_pos + Vector(component.move_offset)).to_tuple())

            local_rot = Rotator(component.rotation)
            lf, lr, lu = local_rot.get_axes()
            wf = lf.rotate_around(Vector(), parent_rot)
            wr = lr.rotate_around(Vector(), parent_rot)
            wu = lu.rotate_around(Vector(), parent_rot)
            component.data.set_rotation(Rotator.from_axes(wf, wr, wu).to_tuple())

    def instantiate(self) -> tuple[Prefab, list[AbstractPlaceable]]:
        """Place the prefab saved by this instance."""
        ret = Prefab(self.name)
        new_components = []
        for component in self.component_data:
            main_obj, new = component.data.instantiate()
            main_obj.set_scale(component.scale)
            main_obj.set_scale3d(component.scale3d)

            new_components.extend(new)
            ret.component_data.append(
                Prefab.ComponentData(
                    main_obj,
                    component.offset.copy(),
                    component.rotation.copy(),
                    component.scale,
                    component.scale3d.copy(),
                    component.move_offset.copy(),
                ),
            )
        ret._location = self._location.copy()
        ret._rotation = self._rotation.copy()
        ret._scale = self._scale
        ret._scale3d = self._scale3d.copy()
        ret._apply_child_world_transform()
        return ret, new_components

    def get_preview(self) -> AbstractPlaceable:
        ret, _ = self.instantiate()
        _, box_extent = ret.get_bounding_box()
        box_extent = Vector(box_extent)
        size = max(box_extent)
        ret.set_scale(1 / size * 20)
        return ret

    def set_preview_location(self, location: tuple[float, float, float]) -> None:
        self.set_location(location)

    def holds_object(self, uobject: unreal.UObject) -> bool:
        if not self.component_data:
            return False
        return any(x.data.holds_object(uobject) for x in self.component_data)

    def set_scale(self, scale: float) -> None:
        self._scale = scale if scale != 0 else self._scale
        for component in self.component_data:
            component.data.set_scale(component.scale * self._scale)
        self._apply_child_world_transform()

    def get_scale(self) -> float:
        return self._scale

    def add_scale(self, scale: float) -> None:
        self.set_scale(self._scale + scale)

    def set_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        self._rotation = list(rotator)
        self._apply_child_world_transform()

    def get_rotation(self) -> list[int]:
        return self._rotation.copy()

    def set_location(self, position: list[float] | tuple[float, float, float]) -> None:
        self._location = list(position)
        self._apply_child_world_transform()

    def destroy(self) -> list[AbstractPlaceable]:
        remove: list[AbstractPlaceable] = [
            self,
        ]
        for component in self.component_data:
            remove.extend(component.data.destroy())

        self.is_destroyed = True
        return remove

    def get_bounding_box(self) -> tuple[Object.Vector, Object.Vector]:
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
        return box_origin.to_ue_vector(), box_extent.to_ue_vector()

    def get_location(self) -> list[float]:
        return self._location

    def add_rotation(self, rotator: tuple[int, int, int]) -> None:
        """Rotate the whole prefab by the given rotator.
        Root object rotates around its own origin, all other objects rotate and move around the root object's origin.
        """
        self._rotation = list((Rotator(self._rotation) + Rotator(rotator)).to_tuple())
        self._apply_child_world_transform()

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

    def get_materials(self) -> list[MaterialInterface]:
        return []

    def set_materials(self, materials: list[MaterialInterface]) -> None:
        pass

    def add_material(self, material: MaterialInterface) -> None:
        super().add_material(material)

    def remove_material(self, material: MaterialInterface | None = None, index: int = -1) -> None:
        super().remove_material(material, index)

    def get_scale3d(self) -> list[float]:
        return self._scale3d.copy()

    def set_scale3d(self, scale3d: list[float]) -> None:
        self._scale3d = [
            scale if scale != 0 else old_scale for scale, old_scale in zip(scale3d, self._scale3d, strict=False)
        ]
        s_x, s_y, s_z = self._scale3d
        for component in self.component_data:
            child = component.data
            c_x, c_y, c_z = component.scale3d
            child.set_scale3d([c_x * s_x, c_y * s_y, c_z * s_z])
        self._apply_child_world_transform()
