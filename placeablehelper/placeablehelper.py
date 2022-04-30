from __future__ import annotations

from abc import ABC, abstractmethod
from time import time
from typing import Dict, List, Optional, Tuple

import unrealsdk
from unrealsdk import *

from .. import bl2tools
from .. import placeables
from .. import settings

import imgui


class PlaceableHelper(ABC):

    def __init__(self, name: str, supported_filters: List[str]):
        self.name: str = name
        self.available_filters: List[str] = supported_filters
        self.objects_by_filter: Dict[str, List[placeables.AbstractPlaceable]] = {f: [] for f in supported_filters}
        self.curr_filter: str = supported_filters[0]
        self.object_index: int = 0
        self.curr_obj: Optional[placeables.AbstractPlaceable] = None
        self.curr_preview: Optional[placeables.AbstractPlaceable] = None
        self.delta_time: float = 0.0
        self.clipboard: Optional[placeables.AbstractPlaceable] = None
        self.b_setup: bool = False

        self.is_cache_dirty: bool = True
        self._cached_objects_for_filter: List[placeables.AbstractPlaceable] = []
        self._cached_names_for_filter: List[str] = []
        self._search_string: str = ""

    def get_filter(self) -> str:
        return self.curr_filter

    def get_index_of_total(self) -> str:
        return f"{self.object_index}/{len(self._cached_objects_for_filter) - 1}"

    def on_enable(self) -> None:
        if self.b_setup:
            self.setup(bl2tools.get_world_info().GetStreamingPersistentMapName().lower())
            self.b_setup = False
        self.is_cache_dirty = True

    def on_disable(self) -> None:
        if self.curr_preview:
            self.curr_preview.destroy()
            self.curr_preview = None
        if self.curr_obj:
            self.curr_obj: placeables.AbstractPlaceable
            self.move_object()  # this will toggle our self.curr_obj to None and handle saving the current attributes

    @abstractmethod
    def add_to_prefab(self) -> None:
        pass

    def add_rotation(self, rotator: tuple) -> None:
        """
        Add rotation to the current held object
        :param rotator:
        :return:
        """
        if self.curr_obj:
            self.curr_obj: placeables.AbstractPlaceable
            self.curr_obj.add_rotation(rotator)

    def add_scale(self, scale: float) -> None:
        """
        Add scale to the current held object
        :param scale:
        :return:
        """
        if self.curr_obj:
            self.curr_obj: placeables.AbstractPlaceable
            self.curr_obj.add_scale(scale)

    @abstractmethod
    def tp_to_selected_object(self, player_controller: unrealsdk.UObject) -> bool:
        """
        Teleport the given PlayerController to the selected object.
        :param player_controller:
        :return: True if TP worked, else False
        """
        pass

    @abstractmethod
    def restore_objects_defaults(self) -> None:
        """
        Restore the objects default values.
        :return:
        """
        pass

    @abstractmethod
    def move_object(self) -> None:
        """
        Start/Stop moving the object.
        :return:
        """
        pass

    def delete_object(self) -> None:
        """
        Delete the current object.
        :return:
        """
        try:
            to_remove = self.curr_obj.destroy()
            for remove_me in to_remove:
                for _list in self.objects_by_filter.values():
                    try:
                        _list.pop(_list.index(remove_me))
                    except ValueError:
                        pass

            self.curr_obj = None
            self.object_index = -1
        except ValueError as e:
            pass  # add to log
        finally:
            self.is_cache_dirty = True

    def copy(self) -> None:
        if self.curr_obj:
            self.clipboard = self.curr_obj
        else:
            self.clipboard = self._cached_objects_for_filter[self.object_index]

    @abstractmethod
    def paste(self) -> None:
        pass

    def calculate_preview(self) -> None:
        if self.curr_preview:
            self.curr_preview.destroy()
        if self.curr_filter == "Create" and settings.b_show_preview:
            self.curr_preview = self._cached_objects_for_filter[self.object_index].get_preview()
        else:
            self.curr_preview = None
        self.delta_time = time()

    def draw_debug_box(self, pc: unrealsdk.UObject) -> None:
        if self.curr_obj:
            self.curr_obj: placeables.AbstractPlaceable
            self.curr_obj.draw_debug_box(pc)

    def get_names_for_filter(self) -> List[str]:
        if self.is_cache_dirty:
            self._cached_objects_for_filter = [
                x for x in self.objects_by_filter.get(self.curr_filter, []) if
                self._search_string.lower() in x.name.lower()
            ]
            self._cached_names_for_filter = [f"{x.name}##{i}" for i, x in enumerate(self._cached_objects_for_filter)]
            self.is_cache_dirty = False
            try:
                valid_index = self._cached_names_for_filter[self.object_index]
            except IndexError:
                self.object_index = -1
        return self._cached_names_for_filter

    def post_render(self, pc: unrealsdk.UObject, offset: int) -> None:
        """
        Handle anything related to the canvas, will be called every game tick post render.
        :param offset:
        :param pc:
        :return:
        """

        imgui.bullet_text(f"Current Object: {'None' if not self.curr_obj else self.curr_obj.name}")
        imgui.bullet_text(f"Clipboard: {'None' if not self.clipboard else self.clipboard.name}")
        imgui.separator()

        combo_index = imgui.combo("Filters", self.available_filters.index(self.curr_filter), self.available_filters)
        if combo_index[0]:
            self._search_string = ""
            self.object_index = -1
            self.is_cache_dirty = True
            self.curr_filter = self.available_filters[combo_index[1]]

        in_text = imgui.input_text("Search", self._search_string, 20)
        if in_text[0]:
            self._search_string = in_text[1]
            self.is_cache_dirty = True

        if imgui.button("Copy"):
            self.copy()
        imgui.same_line()
        if imgui.button("Paste"):
            self.paste()

        if self.curr_obj is None:
            if imgui.button("Edit/Create Selected Object"):
                self.move_object()
        elif imgui.button("Done/ Deselect"):
            self.move_object()
        imgui.same_line()
        if imgui.button("TP To Object"):
            self.tp_to_selected_object(bl2tools.get_player_controller())
        if imgui.button("Delete Object"):
            self.delete_object()

        list_selected = imgui.listbox(f"##{self.curr_filter}",
                                      self.object_index,
                                      self.get_names_for_filter(),
                                      32)
        if list_selected[0]:
            self.object_index = list_selected[1]
            self.calculate_preview()

    def cleanup(self, mapname: str) -> None:
        """
        Do cleanup, called on every Map Load start.
        :param mapname:
        :return:
        """
        self.curr_obj = None
        self.curr_preview = None
        self.object_index = 0
        self.objects_by_filter = {f: [] for f in self.available_filters}
        self.is_cache_dirty = True
        self._search_string = ""

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
