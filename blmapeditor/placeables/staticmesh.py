from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mods_base import ENGINE
from unrealsdk import construct_object, find_all, make_struct, unreal

from .placeable import AbstractPlaceable

if TYPE_CHECKING:
    from common import MaterialInterface, Object, StaticMesh, StaticMeshComponent, WillowGameEngine

    make_vector = Object.Vector.make_struct

    ENGINE = cast(WillowGameEngine, ENGINE)

else:
    make_vector = make_struct


class StaticMeshComponentPlaceable(AbstractPlaceable):
    def __init__(self, name: str, static_mesh: StaticMesh, sm_component: StaticMeshComponent | None = None) -> None:
        super().__init__(name, "StaticMeshComponent")
        self.static_mesh: StaticMesh = static_mesh
        self.sm_component: StaticMeshComponent | None = sm_component  # when destroyed, it will eventually get GC'ed,
        self.sm_component_name: str = ""  # ...but we may still need its name for saving it later to json
        self.uobject_path_name: str = self.static_mesh._path_name()

    def get_materials(self) -> list[MaterialInterface]:
        if self.sm_component:
            return [x for x in self.sm_component.Materials]  # noqa: C416
        return []

    def set_materials(self, materials: list[MaterialInterface]) -> None:
        if self.sm_component and materials is not None:
            self.sm_component.Materials = materials
            self.sm_component.ForceUpdate(False)

    def add_material(self, material: MaterialInterface) -> None:
        super().add_material(material)

    def remove_material(self, material: MaterialInterface | None = None, index: int = -1) -> None:
        super().remove_material(material, index)

    def set_scale(self, scale: float) -> None:
        if not self.sm_component:
            raise ValueError("Cannot set scale on a non-instantiated StaticMeshComponentPlaceable!")
        self.sm_component.SetScale(scale)
        self.sm_component.ForceUpdate(False)
        self.b_default_attributes = False

    def get_scale(self) -> float:
        if not self.sm_component:
            return 1
        return self.sm_component.Scale

    def add_scale(self, scale: float) -> None:
        if not self.sm_component:
            raise ValueError("Cannot add scale on a non-instantiated StaticMeshComponentPlaceable!")
        self.sm_component.SetScale(self.sm_component.Scale + scale)
        self.b_default_attributes = False

    def get_scale3d(self) -> list[float]:
        if not self.sm_component:
            return [1, 1, 1]
        return [self.sm_component.Scale3D.X, self.sm_component.Scale3D.Y, self.sm_component.Scale3D.Z]

    def set_scale3d(self, scale3d: list[float]) -> None:
        if not self.sm_component:
            raise ValueError("Cannot set scale3d on a non-instantiated StaticMeshComponentPlaceable!")
        x, y, z = scale3d
        self.sm_component.Scale3D.X = x
        self.sm_component.Scale3D.Y = y
        self.sm_component.Scale3D.Z = z
        self.sm_component.ForceUpdate(False)
        self.b_default_attributes = False

    def set_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        if not self.sm_component:
            raise ValueError("Cannot set rotation on a non-instantiated StaticMeshComponentPlaceable!")
        pitch, yaw, roll = rotator
        self.sm_component.Rotation.Pitch = pitch
        self.sm_component.Rotation.Yaw = yaw
        self.sm_component.Rotation.Roll = roll
        self.sm_component.ForceUpdate(False)
        self.b_default_attributes = False

    def get_rotation(self) -> list[int]:
        if not self.sm_component:
            return [0, 0, 0]
        return [self.sm_component.Rotation.Pitch, self.sm_component.Rotation.Yaw, self.sm_component.Rotation.Roll]

    def add_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        if not self.sm_component:
            raise ValueError("Cannot add rotation on a non-instantiated StaticMeshComponentPlaceable!")
        pitch, yaw, roll = rotator
        self.sm_component.Rotation.Pitch += pitch
        self.sm_component.Rotation.Yaw += yaw
        self.sm_component.Rotation.Roll += roll
        self.sm_component.ForceUpdate(False)
        self.b_default_attributes = False

    def set_location(self, position: list[float] | tuple[float, float, float]) -> None:
        if not self.sm_component:
            raise ValueError("Cannot set location on a non-instantiated StaticMeshComponentPlaceable!")
        x, y, z = position
        self.sm_component.CachedParentToWorld.WPlane.X = x
        self.sm_component.CachedParentToWorld.WPlane.Y = y
        self.sm_component.CachedParentToWorld.WPlane.Z = z
        self.sm_component.ForceUpdate(False)
        self.sm_component.SetComponentRBFixed(True)

        self.b_default_attributes = False

    def get_location(self) -> list[float]:
        if not self.sm_component:
            return [0, 0, 0]
        return [
            self.sm_component.CachedParentToWorld.WPlane.X,
            self.sm_component.CachedParentToWorld.WPlane.Y,
            self.sm_component.CachedParentToWorld.WPlane.Z,
        ]

    def get_bounding_box(self) -> tuple[Object.Vector, Object.Vector]:
        if self.sm_component:
            bounds = self.sm_component.Bounds
            return (bounds.Origin, bounds.BoxExtent)
        return make_vector("Vector", X=0, Y=0, Z=0), make_vector("Vector", X=0, Y=0, Z=0)

    def instantiate(self) -> tuple[StaticMeshComponentPlaceable, list[StaticMeshComponentPlaceable]]:
        collection_actor = list(find_all("StaticMeshCollectionActor"))[-1]
        new_smc = cast("StaticMeshComponent", construct_object(cls="StaticMeshComponent", outer=collection_actor))
        ret = StaticMeshComponentPlaceable(self.name, self.static_mesh, new_smc)
        new_smc.SetStaticMesh(ret.static_mesh, True)
        new_smc.SetBlockRigidBody(True)
        new_smc.SetActorCollision(True, True, True)
        new_smc.SetTraceBlocking(True, True)
        collection_actor.AttachComponent(new_smc)

        ret.b_dynamically_created = True

        return (ret, [ret])

    def get_preview(self) -> StaticMeshComponentPlaceable:
        world_info = ENGINE.GetCurrentWorldInfo()
        new_smc = world_info.MyEmitterPool.GetFreeStaticMeshComponent(True)
        ret = StaticMeshComponentPlaceable(self.name, self.static_mesh, new_smc)
        assert ret.sm_component is not None, "StaticMeshComponentPlaceable must have a StaticMeshComponent!"

        new_smc.SetStaticMesh(ret.static_mesh, True)
        world_info.MyEmitterPool.AttachComponent(new_smc)
        bounds = ret.sm_component.Bounds
        ret.set_scale(1 / (bounds.SphereRadius / 20))
        ret.b_dynamically_created = True

        return ret

    def set_preview_location(self, location: tuple[float, float, float]) -> None:
        if not self.sm_component:
            raise ValueError("Cannot set location on a non-instantiated StaticMeshComponentPlaceable!")
        x, y, z = location
        self.sm_component.Translation.X = x
        self.sm_component.Translation.Y = y
        self.sm_component.Translation.Z = z

    def holds_object(self, uobject: unreal.UObject) -> bool:
        return self.sm_component is uobject or self.static_mesh is uobject

    def destroy(self) -> list[StaticMeshComponentPlaceable]:
        if self.sm_component is None:  # if we don't have a SMC we can't destroy it
            raise ValueError("Cannot destroy non-instantiated Object!")
        self.sm_component.DetachFromAny()
        self.is_destroyed = True
        return [self]

    def store_default_values(self, default_dict: dict) -> None:
        if self.sm_component and ENGINE.PathName(self.sm_component) not in default_dict:
            default_dict[ENGINE.PathName(self.sm_component)] = {
                "Location": self.get_location(),
                "Rotation": self.get_rotation(),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [ENGINE.PathName(x) for x in self.get_materials()],
            }

    def restore_default_values(self, default_dict: dict) -> None:
        if self.sm_component and ENGINE.PathName(self.sm_component) in default_dict:
            defaults = default_dict[ENGINE.PathName(self.sm_component)]
            self.set_scale(defaults["Scale"])
            self.set_location(defaults["Location"])
            self.set_rotation(defaults["Rotation"])
            self.set_scale3d(defaults["Scale3D"])
            self.set_materials(defaults["Materials"])
            self.b_default_attributes = True

    def save_to_json(self, saved_json: dict) -> None:
        if not self.b_dynamically_created and self.b_default_attributes and not self.is_destroyed:
            return

        cleaned_tags: list[str] = [x.strip() for x in self.tags if x.strip()]

        if not self.b_dynamically_created and not self.b_default_attributes and not self.is_destroyed:
            smc_list = saved_json.setdefault("Edit", {}).setdefault("StaticMeshComponent", {})
            smc_list[ENGINE.PathName(self.sm_component)] = {
                "Rename": self.rename,
                "Tags": cleaned_tags,
                "Metadata": self.metadata,
                "Location": self.get_location(),
                "Rotation": self.get_rotation(),
                "Scale": self.get_scale(),
                "Scale3D": self.get_scale3d(),
                "Materials": [ENGINE.PathName(x) for x in self.get_materials()],
            }

        elif not self.b_dynamically_created and self.is_destroyed:
            smc_list = saved_json.setdefault("Destroy", {}).setdefault("StaticMeshComponent", [])
            smc_list.append(self.sm_component_name)

        elif self.b_dynamically_created:
            smc_list = saved_json.setdefault("Create", {}).setdefault("StaticMesh", [])
            smc_list.append(
                {
                    self.uobject_path_name: {
                        "Rename": self.rename,
                        "Tags": cleaned_tags,
                        "Metadata": self.metadata,
                        "Location": self.get_location(),
                        "Rotation": self.get_rotation(),
                        "Scale": self.get_scale(),
                        "Scale3D": self.get_scale3d(),
                        "Materials": [ENGINE.PathName(x) for x in self.get_materials()],
                    },
                },
            )
