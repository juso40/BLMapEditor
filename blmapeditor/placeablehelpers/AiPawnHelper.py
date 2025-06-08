from __future__ import annotations

from typing import TYPE_CHECKING, cast

from mods_base import ENGINE
from unrealsdk import find_all, find_object

from .. import placeables
from .placeablehelper import PlaceableHelper

if TYPE_CHECKING:
    from common import AIPawnBalanceDefinition, MaterialInterface


class AiPawnHelper(PlaceableHelper):
    def __init__(self) -> None:
        super().__init__(name="Pawns", supported_filters=["All Instances", "Create", "Edited"])

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

    def restore_objects_defaults(self) -> None:
        return

    def cleanup(self, mapname: str) -> None:
        super().cleanup(mapname)

    def setup(self, mapname: str) -> None:
        if mapname in ("menumap", "none", ""):
            return

        self.objects_by_filter["Create"].extend(
            [
                placeables.AIPawnPlaceable(
                    x.PlayThroughs[0].DisplayName
                    if (x.PlayThroughs and x.PlayThroughs[0].DisplayName)
                    else ENGINE.PathName(x).split(".")[-1],
                    x,
                )
                for x in cast(list["AIPawnBalanceDefinition"], list(find_all("AIPawnBalanceDefinition"))[1:])
            ],
        )

        self.objects_by_filter["Create"].sort(key=lambda obj: obj.name)

    def load_map(self, map_data: dict) -> None:
        for bp in map_data.get("Create", {}).get("AIPawnBalanceDefinition", []):
            for obj, attrs in bp.items():
                for pawn_bp in cast(list[placeables.AIPawnPlaceable], self.objects_by_filter["Create"]):
                    if pawn_bp.holds_object(find_object("AIPawnBalanceDefinition", obj)):
                        new_instance, _ = pawn_bp.instantiate()
                        new_instance: placeables.AIPawnPlaceable

                        new_instance.rename = attrs.get("Rename", "")
                        new_instance.tags = attrs.get("Tags", [])
                        new_instance.metadata = attrs.get("Metadata", "")
                        new_instance.set_location(attrs.get("Location", (0, 0, 0)))
                        new_instance.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                        new_instance.set_scale(attrs.get("Scale", 1))
                        new_instance.set_scale3d(attrs.get("Scale3D", (1, 1, 1)))

                        mats = attrs.get("Materials", None)
                        if mats is not None:
                            mats = [cast("MaterialInterface", find_object("MaterialInterface", m)) for m in mats]
                        new_instance.set_materials(mats)

                        self.objects_by_filter["Edited"].append(new_instance)
                        break

    def save_map(self, map_data: dict) -> None:
        for placeable in self.objects_by_filter["Edited"]:
            placeable.save_to_json(map_data)
