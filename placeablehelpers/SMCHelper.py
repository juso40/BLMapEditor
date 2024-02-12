import contextlib
from typing import List, cast

import unrealsdk  # type: ignore

from .. import bl2tools, placeables
from .placeablehelper import PlaceableHelper


class SMCHelper(PlaceableHelper):
    def __init__(self) -> None:
        super().__init__(
            name="Static Meshes",
            supported_filters=["All Instances", "Edited", "Create"],
        )

    def on_enable(self) -> None:
        super().on_enable()

    def on_disable(self) -> None:
        super().on_disable()

    def add_to_prefab(self) -> None:
        super().add_to_prefab()

    def get_filter(self) -> str:
        return super().get_filter()

    def get_index_of_total(self) -> str:
        return super().get_index_of_total()

    def cleanup(self, mapname: str) -> None:
        super().cleanup(mapname)
        self.edited_default.clear()
        self.deleted.clear()

    def setup(self, mapname: str) -> None:
        if mapname in ("menumap", "none", ""):
            return

        for x in unrealsdk.FindAll("StaticMeshCollectionActor"):
            self.objects_by_filter["All Instances"].extend(
                [
                    placeables.StaticMeshComponent(
                        bl2tools.get_obj_path_name(y.StaticMesh).split(".", 1)[-1],
                        y.StaticMesh,
                        y,
                    )
                    for y in x.AllComponents
                ],
            )
        self.objects_by_filter["All Instances"].sort(key=lambda obj: obj.name)

        for mesh in unrealsdk.FindAll("StaticMesh")[1:]:
            self.objects_by_filter["Create"].append(
                placeables.StaticMeshComponent(bl2tools.get_obj_path_name(mesh).split(".", 1)[-1], mesh),
            )

        self.objects_by_filter["Create"].sort(key=lambda _x: _x.name)

    def load_map(self, map_data: dict) -> None:
        for to_destroy in map_data.get("Destroy", {}).get("StaticMeshComponent", []):
            for placeable in cast(List[placeables.StaticMeshComponent], self.objects_by_filter["All Instances"]):
                if placeable.holds_object(unrealsdk.FindObject("Object", to_destroy)):
                    self.deleted.append(placeable)
                    to_remove: List[placeables.StaticMeshComponent] = placeable.destroy()
                    for remove_me in to_remove:
                        for _list in self.objects_by_filter.values():
                            with contextlib.suppress(ValueError):
                                _list.pop(_list.index(remove_me))
                    break

        for bp in map_data.get("Create", {}).get("StaticMesh", []):
            for obj, attrs in bp.items():
                for smc_bp in cast(List[placeables.StaticMeshComponent], self.objects_by_filter["Create"]):
                    if smc_bp.holds_object(unrealsdk.FindObject("Object", obj)):
                        new_instance, created_smcs = smc_bp.instantiate()
                        new_instance: placeables.StaticMeshComponent

                        new_instance.rename = attrs.get("Rename", "")
                        new_instance.tags = attrs.get("Tags", [])
                        new_instance.metadata = attrs.get("Metadata", "")
                        new_instance.set_location(attrs.get("Location", (0, 0, 0)))
                        new_instance.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                        new_instance.set_scale(attrs.get("Scale", 1))
                        new_instance.set_scale3d(attrs.get("Scale3D", (1, 1, 1)))

                        mats = attrs.get("Materials", None)
                        if mats is not None:
                            mats = [unrealsdk.FindObject("MaterialInstanceConstant", m) for m in mats]
                        new_instance.set_materials(mats)

                        self.objects_by_filter["Edited"].append(new_instance)
                        self.objects_by_filter["All Instances"].append(new_instance)
                        break

        for obj, attrs in map_data.get("Edit", {}).get("StaticMeshComponent", {}).items():
            for placeable in cast(List[placeables.StaticMeshComponent], self.objects_by_filter["All Instances"]):
                if placeable.holds_object(unrealsdk.FindObject("Object", obj)):
                    placeable: placeables.StaticMeshComponent
                    placeable.rename = attrs.get("Rename", "")
                    placeable.tags = attrs.get("Tags", [])
                    placeable.metadata = attrs.get("Metadata", "")
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
        for placeable in self.objects_by_filter["All Instances"]:
            placeable.save_to_json(map_data)

        for deleted in self.deleted:
            deleted.save_to_json(map_data)
