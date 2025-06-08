from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, cast

from mods_base import ENGINE
from unrealsdk import find_all, find_object, unreal

from .. import placeables
from .placeablehelper import PlaceableHelper

if TYPE_CHECKING:
    from common import (
        MaterialInterface,
        WillowGameEngine,
        WillowInteractiveObject,
        WillowVendingMachine,
        WillowVendingMachineBlackMarket,
    )

    ENGINE = cast(WillowGameEngine, ENGINE)


class InterctiveObjectHelper(PlaceableHelper):
    def __init__(self) -> None:
        super().__init__(name="Interactive Objects", supported_filters=["All Instances", "Create", "Edited"])

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

    def tp_to_selected_object(self, pc: unreal.UObject) -> bool:
        if self.curr_filter == "Create":
            return False
        pc.Location = tuple(self._cached_objects_for_filter[self.object_index].get_location())
        return True

    def cleanup(self, mapname: str) -> None:
        super().cleanup(mapname)
        self.edited_default.clear()
        self.deleted.clear()

    def setup(self, mapname: str) -> None:
        if mapname in ("menumap", "none", ""):
            return

        self.objects_by_filter["All Instances"].extend(
            [
                placeables.InteractiveObjectPlaceable(
                    ENGINE.PathName(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                    if x.BalanceDefinitionState.BalanceDefinition
                    else ENGINE.PathName(x.InteractiveObjectDefinition).split(".")[-1],
                    x.BalanceDefinitionState.BalanceDefinition
                    if x.BalanceDefinitionState.BalanceDefinition
                    else x.InteractiveObjectDefinition,
                    x,
                )
                for x in cast(
                    list["WillowInteractiveObject"],
                    list(find_all("WillowInteractiveObject"))[1:],
                )
            ],
        )
        self.objects_by_filter["All Instances"].extend(
            [
                placeables.InteractiveObjectPlaceable(
                    ENGINE.PathName(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                    if x.BalanceDefinitionState.BalanceDefinition
                    else ENGINE.PathName(x.InteractiveObjectDefinition).split(".")[-1],
                    x.BalanceDefinitionState.BalanceDefinition
                    if x.BalanceDefinitionState.BalanceDefinition
                    else x.InteractiveObjectDefinition,
                    x,
                )
                for x in cast(
                    list["WillowVendingMachine"],
                    list(find_all("WillowVendingMachine"))[1:],
                )
            ],
        )
        self.objects_by_filter["All Instances"].extend(
            [
                placeables.InteractiveObjectPlaceable(
                    ENGINE.PathName(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                    if x.BalanceDefinitionState.BalanceDefinition
                    else ENGINE.PathName(x.InteractiveObjectDefinition).split(".")[-1],
                    x.BalanceDefinitionState.BalanceDefinition
                    if x.BalanceDefinitionState.BalanceDefinition
                    else x.InteractiveObjectDefinition,
                    x,
                )
                for x in cast(
                    list["WillowVendingMachineBlackMarket"],
                    list(find_all("WillowVendingMachineBlackMarket"))[1:],
                )
            ],
        )
        self.objects_by_filter["All Instances"].sort(key=lambda obj: obj.name)
        #############################################################################

        interactives = list(find_all("InteractiveObjectBalanceDefinition"))[1:]  # type: list
        do_not_add = tuple(x.DefaultInteractiveObject for x in interactives)
        interactives.extend([x for x in list(find_all("InteractiveObjectDefinition"))[1:] if x not in do_not_add])

        black_listed = [
            ("InteractiveObjectDefinition", "GD_Episode12Data.InteractiveObjects.InfoKiosk"),
            ("InteractiveObjectDefinition", "GD_Z2_TrailerTrashinData.InteractiveObjects.IO_MO_PropaneTanks"),
            ("InteractiveObjectBalanceDefinition", "GD_Z2_TrailerTrashinData.BalanceDefs.BD_PropaneTank"),
        ]
        for _class, _object in black_listed:
            with contextlib.suppress(ValueError):
                interactives.pop(interactives.index(find_object(_class, _object)))

        self.objects_by_filter["Create"].extend(
            [placeables.InteractiveObjectPlaceable(ENGINE.PathName(x).split(".")[-1], x) for x in interactives],
        )
        self.objects_by_filter["Create"].sort(key=lambda obj: obj.name)

    def load_map(self, map_data: dict) -> None:
        for to_destroy in map_data.get("Destroy", {}).get("InteractiveObjectDefinition", []):
            for placeable in cast(
                list[placeables.InteractiveObjectPlaceable],
                self.objects_by_filter["All Instances"],
            ):
                if placeable.holds_object(find_object("Object", to_destroy)):
                    self.deleted.append(placeable)
                    to_remove: list[placeables.InteractiveObjectPlaceable] = placeable.destroy()
                    for remove_me in to_remove:
                        for _list in self.objects_by_filter.values():
                            with contextlib.suppress(ValueError):
                                _list.pop(_list.index(remove_me))
                    break

        for bp in map_data.get("Create", {}).get("InteractiveObjectDefinition", []):
            for obj, attrs in bp.items():
                for iodef in cast(
                    list[placeables.InteractiveObjectPlaceable],
                    self.objects_by_filter["Create"],
                ):
                    if iodef.holds_object(find_object("Object", obj)):
                        new_instance, _ = iodef.instantiate()
                        new_instance: placeables.InteractiveObjectPlaceable

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
                        self.objects_by_filter["All Instances"].append(new_instance)
                        break

        for obj, attrs in map_data.get("Edit", {}).get("InteractiveObjectDefinition", {}).items():
            for placeable in cast(
                list[placeables.InteractiveObjectPlaceable],
                self.objects_by_filter["All Instances"],
            ):
                if placeable.holds_object(find_object("Object", obj)):
                    placeable: placeables.InteractiveObjectPlaceable
                    placeable.rename = attrs.get("Rename", "")
                    placeable.tags = attrs.get("Tags", [])
                    placeable.metadata = attrs.get("Metadata", "")
                    placeable.set_location(attrs.get("Location", (0, 0, 0)))
                    placeable.set_rotation(attrs.get("Rotation", (0, 0, 0)))
                    placeable.set_scale(attrs.get("Scale", 1))
                    placeable.set_scale3d(attrs.get("Scale3D", (1, 1, 1)))

                    mats = attrs.get("Materials", None)
                    if mats is not None:
                        mats = [cast("MaterialInterface", find_object("MaterialInterface", m)) for m in mats]
                    placeable.set_materials(mats)

                    self.objects_by_filter["Edited"].append(placeable)
                    break

    def save_map(self, map_data: dict) -> None:
        for placeable in self.objects_by_filter["All Instances"]:
            placeable.save_to_json(map_data)

        for deleted in self.deleted:
            deleted.save_to_json(map_data)
