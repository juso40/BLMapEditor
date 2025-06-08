from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from coroutines import Time
from mods_base import ENGINE, get_pc
from uemath import Vector
from unrealsdk import make_struct

from .. import placeables, prefabbuffer, settings
from .. import selectedobject as sobj

if TYPE_CHECKING:
    from common import Object, WillowGameEngine, WillowPlayerController

    make_vector = Object.Vector.make_struct
    ENGINE = cast(WillowGameEngine, ENGINE)
else:
    make_vector = make_struct


class PlaceableHelper(ABC):
    def __init__(self, name: str, supported_filters: list[str]) -> None:
        self.name: str = name
        self.available_filters: list[str] = supported_filters
        self.objects_by_filter: dict[str, list[placeables.AbstractPlaceable]] = {f: [] for f in supported_filters}
        self.curr_filter: str = supported_filters[0]
        self.object_index: int = 0
        self.b_setup: bool = False
        self.edited_default: dict = {}
        self.search_string: str = ""
        self.deleted: list[placeables.AbstractPlaceable] = []

        self.is_cache_dirty: bool = True
        self._cached_objects_for_filter: list[placeables.AbstractPlaceable] = []
        self._cached_names_for_filter: list[str] = []
        self._object_renames: dict[str, str] = {}
        self._last_tick: float = Time.time

    def __str__(self) -> str:
        return self.name

    def get_filter(self) -> str:
        return self.curr_filter

    def get_index_of_total(self) -> str:
        return f"{self.object_index}/{len(self._cached_objects_for_filter) - 1}"

    def get_selected_object(self) -> placeables.AbstractPlaceable | None:
        try:
            return self._cached_objects_for_filter[self.object_index]
        except IndexError:
            return None

    def on_enable(self) -> None:
        if self.b_setup:
            self.setup(ENGINE.GetCurrentWorldInfo().GetStreamingPersistentMapName().lower())
            self.b_setup = False
            self.is_cache_dirty = True

    def on_disable(self) -> None:
        sobj.destroy_preview()

    def add_to_prefab(self) -> None:
        if self.curr_filter != "Create":
            try:
                prefabbuffer.prefab_buffer.pop(
                    prefabbuffer.prefab_buffer.index(self._cached_objects_for_filter[self.object_index]),
                )  # toggle, remove if already in list
            except ValueError:
                with contextlib.suppress(IndexError):
                    prefabbuffer.prefab_buffer.append(self._cached_objects_for_filter[self.object_index])

    def tp_to_selected_object(self, player_controller: WillowPlayerController) -> bool:
        """
        Teleport the given PlayerController to the selected object.

        :param player_controller:
        :return: True if TP worked, else False
        """
        if self.curr_filter in ("Create", "Prefab BP"):
            return False
        try:
            target = Vector(self._cached_objects_for_filter[self.object_index].get_location())
        except IndexError:
            return False

        pc_forward = Vector(player_controller.CalcViewRotation)
        player_controller.Location = (target - pc_forward * 200).to_ue_vector()
        return True

    def restore_objects_defaults(self) -> None:
        """
        Restore the objects default values.

        :return:
        """
        if self.curr_filter in ("Create", "Prefab BP"):
            return

        if sobj.SELECTED_OBJECT:
            sobj.SELECTED_OBJECT.restore_default_values(self.edited_default)
            if not sobj.SELECTED_OBJECT.b_dynamically_created:
                self.objects_by_filter["Edited"].pop(self.objects_by_filter["Edited"].index(sobj.SELECTED_OBJECT))
                self.object_index %= len(self._cached_objects_for_filter)
            sobj.SELECTED_OBJECT = None

        self.is_cache_dirty = True

    def move_object(self) -> None:
        """
        Start/Stop moving the object.

        :return:
        """
        if sobj.SELECTED_OBJECT:
            sobj.SELECTED_OBJECT = None  # stop editing this object, will stay in position
        elif self.curr_filter != "Create":
            sobj.SELECTED_OBJECT = self._cached_objects_for_filter[self.object_index]
            # add the default values to the default dict to revert changes if needed
            sobj.SELECTED_OBJECT.store_default_values(self.edited_default)
            if sobj.SELECTED_OBJECT not in self.objects_by_filter["Edited"]:
                self.objects_by_filter["Edited"].append(sobj.SELECTED_OBJECT)
        elif self.curr_filter == "Create":
            # create a new instance from our Blueprint object
            new_instance, created = self._cached_objects_for_filter[self.object_index].instantiate()
            for _o in created:
                self.objects_by_filter["Edited"].append(_o)
                self.objects_by_filter["All Instances"].append(_o)
            sobj.SELECTED_OBJECT = new_instance  # let's start editing this new object
        self.is_cache_dirty = True

    def cancel_editing(self) -> None:
        if sobj.SELECTED_OBJECT:
            self.curr_obj: placeables.AbstractPlaceable
            if sobj.SELECTED_OBJECT.b_dynamically_created:
                self.delete_object()
            else:
                self.restore_objects_defaults()

    def delete_object(self) -> None:
        """Delete the current object."""
        to_delete: placeables.AbstractPlaceable = (
            sobj.SELECTED_OBJECT or self._cached_objects_for_filter[self.object_index]
        )
        if cast(placeables.AbstractPlaceable, to_delete).b_dynamically_created and to_delete not in self.deleted:
            self.deleted.append(to_delete)
        try:
            to_remove: list[placeables.AbstractPlaceable] = to_delete.destroy()
            for remove_me in to_remove:
                for _list in self.objects_by_filter.values():
                    with contextlib.suppress(ValueError):
                        _list.pop(_list.index(remove_me))
            if sobj.SELECTED_OBJECT is not None:  # if we deleted the selected object, we need to deselect it
                sobj.SELECTED_OBJECT = None
            if self.curr_filter not in ("Create", "Prefabs Blueprints"):  # In create mode we can stay at our index
                self.object_index = -1
        except ValueError:
            pass
        finally:
            self.is_cache_dirty = True

    def copy(self) -> None:
        if sobj.SELECTED_OBJECT:
            sobj.CLIPBOARD = sobj.SELECTED_OBJECT
        else:
            try:
                sobj.CLIPBOARD = self._cached_objects_for_filter[self.object_index]
            except IndexError:
                self.object_index = -1
                self.is_cache_dirty = True
                return
        sobj.CLIPBOARD_HELPER = self

    def paste(self) -> None:
        if sobj.CLIPBOARD and not sobj.CLIPBOARD.is_destroyed:
            pasted, created = sobj.CLIPBOARD.instantiate()
            pasted.rename = sobj.CLIPBOARD.rename
            pasted.set_scale(sobj.CLIPBOARD.get_scale())
            pasted.set_rotation(sobj.CLIPBOARD.get_rotation())
            pasted.set_scale3d(sobj.CLIPBOARD.get_scale3d())
            pasted.set_materials(sobj.CLIPBOARD.get_materials())
            pasted.set_location(sobj.CLIPBOARD.get_location())
            pasted.b_dynamically_created = True
            self.objects_by_filter["Edited"].extend(created)
            self.objects_by_filter["All Instances"].extend(created)
            if not sobj.SELECTED_OBJECT:
                sobj.SELECTED_OBJECT = pasted
        self.is_cache_dirty = True

    def update_preview(self) -> None:
        if settings.b_show_preview:
            sobj.set_preview(self._cached_objects_for_filter[self.object_index].get_preview())
        else:
            sobj.destroy_preview()

    def _update_caches(self) -> None:
        pc = get_pc()
        pc_loc: tuple[float, float, float] = (pc.Location.X, pc.Location.Y, pc.Location.Z)

        search_string = self.search_string.lower()
        to_filter = self.objects_by_filter.get(self.curr_filter, [])
        if search_string:
            to_filter = [x for x in to_filter if search_string in (x.rename if x.rename else x.name).lower()]
        if settings.editor_filter_range != 0:
            to_filter = [
                x
                for x in to_filter
                if sum((a - b) * (a - b) for a, b in zip(x.get_location(), pc_loc, strict=False))
                < (settings.editor_filter_range * 50) * (settings.editor_filter_range * 50)
            ]
        if settings.sort_by_distance:
            to_filter.sort(key=lambda x: sum([(a - b) ** 2 for a, b in zip(x.get_location(), pc_loc, strict=False)]))

        self._cached_objects_for_filter = to_filter
        # The respective names for the object list from above
        self._cached_names_for_filter = [
            f"{x.rename if x.rename else x.name}##{i}" for i, x in enumerate(self._cached_objects_for_filter)
        ]

        self.is_cache_dirty = False  # We are up-to-date now
        try:
            _ = self._cached_names_for_filter[self.object_index]
        except IndexError:
            self.object_index = -1

    def get_names_for_filter(self) -> list[str]:
        if self.is_cache_dirty or settings.sort_by_distance:  # Update the cached objects and names
            if settings.sort_by_distance and self.curr_filter not in ("Create", "Prefabs Blueprints"):
                # check if at least 2 second have passed since the last update
                if Time.time - self._last_tick < 2:
                    self.is_cache_dirty = False
                    return self._cached_names_for_filter
                self._last_tick = Time.time
            self._update_caches()
        return self._cached_names_for_filter

    def cleanup(self, _mapname: str) -> None:
        """Do cleanup, called on every Map Load start."""
        self.object_index = 0
        self.objects_by_filter = {f: [] for f in self.available_filters}
        self.is_cache_dirty = True
        self.search_string = ""

    @abstractmethod
    def setup(self, mapname: str) -> None:
        """
        Setup anything needed for editing, gets called every Map Load finished.

        :param mapname:
        :return:
        """
        pass

    @abstractmethod
    def load_map(self, map_data: dict) -> None:
        """
        Apply any settings from the given map data.

        :param map_data:
        :return:
        """
        pass

    @abstractmethod
    def save_map(self, map_data: dict) -> None:
        """
        Write all map changes into the given map_data dict.

        :param map_data:
        :return:
        """
        pass
