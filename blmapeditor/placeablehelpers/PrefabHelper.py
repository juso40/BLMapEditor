from __future__ import annotations

import pathlib
from typing import cast

from uemath import Vector
from unrealsdk import unreal

from .. import placeables, prefabbuffer
from .. import selectedobject as sobj
from ..placeablehelpers import InteractiveHelper, PawnHelper, SMCHelper
from .placeablehelper import PlaceableHelper


class PrefabHelper(PlaceableHelper):
    def __init__(self) -> None:
        super().__init__(
            name="Prefabs",
            supported_filters=["Prefab Blueprints", "Prefab Instances"],
        )

    def on_enable(self) -> None:
        super().on_enable()

    def on_disable(self) -> None:
        super().on_disable()

    def add_to_prefab(self) -> None:
        pass

    def _create_and_add_to_filters(self) -> placeables.Prefab:
        # create a new instance from our Blueprint object
        new_instance, created_objs = self._cached_objects_for_filter[self.object_index].instantiate()
        for c_obj in created_objs:  # filter created object to its correct HelperClass object_by_filter list
            if isinstance(c_obj, placeables.StaticMeshComponentPlaceable):
                SMCHelper.objects_by_filter["Edited"].append(c_obj)
                SMCHelper.objects_by_filter["All Instances"].append(c_obj)
            elif isinstance(c_obj, placeables.InteractiveObjectPlaceable):
                InteractiveHelper.objects_by_filter["Edited"].append(c_obj)
                InteractiveHelper.objects_by_filter["All Instances"].append(c_obj)
            elif isinstance(c_obj, placeables.AIPawnPlaceable):
                PawnHelper.objects_by_filter["Edited"].append(c_obj)
                PawnHelper.objects_by_filter["All Instances"].append(c_obj)
        return cast(placeables.Prefab, new_instance)

    def paste(self) -> None:
        if sobj.CLIPBOARD and not sobj.CLIPBOARD.is_destroyed:
            pasted = self._create_and_add_to_filters()
            pasted.rename = sobj.CLIPBOARD.rename
            pasted.set_scale(sobj.CLIPBOARD.get_scale())
            pasted.set_rotation(sobj.CLIPBOARD.get_rotation())
            pasted.set_scale3d(sobj.CLIPBOARD.get_scale3d())
            pasted.set_materials(sobj.CLIPBOARD.get_materials())
            pasted.set_location(sobj.CLIPBOARD.get_location())
            pasted.b_dynamically_created = True
            self.objects_by_filter["Prefab Instances"].append(pasted)
            if not sobj.SELECTED_OBJECT:
                sobj.SELECTED_OBJECT = pasted
        self.is_cache_dirty = True

    def get_filter(self) -> str:
        return super().get_filter()

    def get_index_of_total(self) -> str:
        return super().get_index_of_total()

    def tp_to_selected_object(self, pc: unreal.UObject) -> bool:
        if self.curr_filter in ("Prefab Blueprints",):
            return False
        target = Vector(self._cached_objects_for_filter[self.object_index].get_location())
        pc_forward = Vector(pc.CalcViewRotation) * 200
        pc.Location = (target - pc_forward).to_tuple()
        return True

    def restore_objects_defaults(self) -> None:
        return

    def move_object(self) -> None:
        if sobj.SELECTED_OBJECT:
            sobj.SELECTED_OBJECT = None
        else:
            if not self._cached_objects_for_filter:
                return
            if self.curr_filter != "Prefab Blueprints":
                sobj.SELECTED_OBJECT = self._cached_objects_for_filter[self.object_index]
            elif self.curr_filter == "Prefab Blueprints":
                new_instance = self._create_and_add_to_filters()
                new_instance.b_dynamically_created = True
                sobj.SELECTED_OBJECT = new_instance  # let's start editing this new object
                self.objects_by_filter["Prefab Instances"].append(new_instance)
        self.is_cache_dirty = True

    def cleanup(self, mapname: str) -> None:
        super().cleanup(mapname)
        prefabbuffer.prefab_buffer.clear()

    def setup(self, mapname: str) -> None:
        if mapname in ("menumap", "none", ""):
            return

        # ToDo: Load the prefabs from the json data
        # The json should be stored in MapEditor/Prefabs/<prefab_name>.json
        for p in (pathlib.Path(__file__).parent.parent / "Prefabs").glob("*.json"):
            blueprint = placeables.Prefab.load_prefab_json(
                p.name.replace(".json", "").replace("_", " ").split(maxsplit=1)[-1],
            )
            if blueprint:
                self.objects_by_filter["Prefab Blueprints"].append(blueprint)

    def load_map(self, map_data: dict) -> None:
        pass  # ToDo: Should Prefabs save their instanced data?

    def save_map(self, map_data: dict) -> None:
        pass
