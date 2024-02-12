import contextlib
from typing import List, cast

import unrealsdk  # type: ignore

from .. import bl2tools, placeables
from .placeablehelper import PlaceableHelper


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

    def tp_to_selected_object(self, pc: unrealsdk.UObject) -> bool:
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
                placeables.InteractiveObjectBalanceDefinition(
                    bl2tools.get_obj_path_name(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                    if x.BalanceDefinitionState.BalanceDefinition
                    else bl2tools.get_obj_path_name(x.InteractiveObjectDefinition).split(".")[-1],
                    x.BalanceDefinitionState.BalanceDefinition
                    if x.BalanceDefinitionState.BalanceDefinition
                    else x.InteractiveObjectDefinition,
                    x,
                )
                for x in unrealsdk.FindAll("WillowInteractiveObject")[1:]
            ],
        )
        self.objects_by_filter["All Instances"].extend(
            [
                placeables.InteractiveObjectBalanceDefinition(
                    bl2tools.get_obj_path_name(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                    if x.BalanceDefinitionState.BalanceDefinition
                    else bl2tools.get_obj_path_name(x.InteractiveObjectDefinition).split(".")[-1],
                    x.BalanceDefinitionState.BalanceDefinition
                    if x.BalanceDefinitionState.BalanceDefinition
                    else x.InteractiveObjectDefinition,
                    x,
                )
                for x in unrealsdk.FindAll("WillowVendingMachine")[1:]
            ],
        )
        self.objects_by_filter["All Instances"].extend(
            [
                placeables.InteractiveObjectBalanceDefinition(
                    bl2tools.get_obj_path_name(x.BalanceDefinitionState.BalanceDefinition).split(".")[-1]
                    if x.BalanceDefinitionState.BalanceDefinition
                    else bl2tools.get_obj_path_name(x.InteractiveObjectDefinition).split(".")[-1],
                    x.BalanceDefinitionState.BalanceDefinition
                    if x.BalanceDefinitionState.BalanceDefinition
                    else x.InteractiveObjectDefinition,
                    x,
                )
                for x in unrealsdk.FindAll("WillowVendingMachineBlackMarket")[1:]
            ],
        )
        self.objects_by_filter["All Instances"].sort(key=lambda obj: obj.name)
        #############################################################################

        interactives = unrealsdk.FindAll("InteractiveObjectBalanceDefinition")[1:]  # type: list
        do_not_add = tuple(x.DefaultInteractiveObject for x in interactives)
        interactives.extend([x for x in unrealsdk.FindAll("InteractiveObjectDefinition")[1:] if x not in do_not_add])

        black_listed = [
            ("InteractiveObjectDefinition", "GD_Episode12Data.InteractiveObjects.InfoKiosk"),
            ("InteractiveObjectDefinition", "GD_Z2_TrailerTrashinData.InteractiveObjects.IO_MO_PropaneTanks"),
            ("InteractiveObjectBalanceDefinition", "GD_Z2_TrailerTrashinData.BalanceDefs.BD_PropaneTank"),
        ]
        for _class, _object in black_listed:
            with contextlib.suppress(ValueError):
                interactives.pop(interactives.index(unrealsdk.FindObject(_class, _object)))

        self.objects_by_filter["Create"].extend(
            [
                placeables.InteractiveObjectBalanceDefinition(bl2tools.get_obj_path_name(x).split(".")[-1], x)
                for x in interactives
            ],
        )
        self.objects_by_filter["Create"].sort(key=lambda obj: obj.name)

    def load_map(self, map_data: dict) -> None:
        for to_destroy in map_data.get("Destroy", {}).get("InteractiveObjectDefinition", []):
            for placeable in cast(
                List[placeables.InteractiveObjectBalanceDefinition],
                self.objects_by_filter["All Instances"],
            ):
                if placeable.holds_object(unrealsdk.FindObject("Object", to_destroy)):
                    self.deleted.append(placeable)
                    to_remove: List[placeables.InteractiveObjectBalanceDefinition] = placeable.destroy()
                    for remove_me in to_remove:
                        for _list in self.objects_by_filter.values():
                            with contextlib.suppress(ValueError):
                                _list.pop(_list.index(remove_me))
                    break

        for bp in map_data.get("Create", {}).get("InteractiveObjectDefinition", []):
            for obj, attrs in bp.items():
                for iodef in cast(
                    List[placeables.InteractiveObjectBalanceDefinition],
                    self.objects_by_filter["Create"],
                ):
                    if iodef.holds_object(unrealsdk.FindObject("Object", obj)):
                        new_instance, _ = iodef.instantiate()
                        new_instance: placeables.InteractiveObjectBalanceDefinition

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

        for obj, attrs in map_data.get("Edit", {}).get("InteractiveObjectDefinition", {}).items():
            for placeable in cast(
                List[placeables.InteractiveObjectBalanceDefinition],
                self.objects_by_filter["All Instances"],
            ):
                if placeable.holds_object(unrealsdk.FindObject("Object", obj)):
                    placeable: placeables.InteractiveObjectBalanceDefinition
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
