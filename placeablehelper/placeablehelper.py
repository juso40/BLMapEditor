from __future__ import annotations

from abc import ABC, abstractmethod
from time import time
from typing import Dict, List, Optional, Tuple

import unrealsdk
from unrealsdk import *

from .. import bl2tools
from .. import placeables
from .. import settings


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

    def get_filter(self) -> str:
        return self.curr_filter

    def get_index_of_total(self) -> str:
        return f"{self.object_index}/{len(self.objects_by_filter[self.curr_filter]) - 1}"

    @abstractmethod
    def on_command(self, command: str) -> bool:
        """
        Each editor mode should handle their own commands
        :param command:
        :return:
        """
        pass

    def on_enable(self) -> None:
        if self.b_setup:
            self.setup(bl2tools.get_world_info().GetStreamingPersistentMapName().lower())
            self.b_setup = False

    def on_disable(self) -> None:
        if self.curr_preview:
            self.curr_preview.destroy()
            self.curr_preview = None
        self.curr_obj = None

    def change_filter(self) -> None:
        """
        Change the objects filter.
        :return:
        """

        self.curr_obj = None
        self.curr_filter = self.available_filters[
            (self.available_filters.index(self.curr_filter) + 1) % len(self.available_filters)
            ]
        if not any(self.objects_by_filter.values()):
            return
        while not self.objects_by_filter[self.curr_filter]:  # Edited/prefabs may be empty
            self.curr_filter = self.available_filters[
                (self.available_filters.index(self.curr_filter) + 1) % len(self.available_filters)
                ]
        self.object_index = 0

    def index_up(self) -> Tuple[str, List[placeables.AbstractPlaceable], int]:
        self.object_index = (self.object_index + 1) % len(self.objects_by_filter[self.curr_filter])
        return self.curr_filter, self.objects_by_filter[self.curr_filter], self.object_index

    def index_down(self) -> Tuple[str, List[placeables.AbstractPlaceable], int]:
        self.object_index = (self.object_index - 1) % len(self.objects_by_filter[self.curr_filter])
        return self.curr_filter, self.objects_by_filter[self.curr_filter], self.object_index

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
    def move_object(self, b_move: bool) -> None:
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
            if not self.objects_by_filter[self.curr_filter]:
                self.change_filter()
                self.object_index = 0
            else:
                self.object_index = (self.object_index - 1) % len(self.objects_by_filter[self.curr_filter])
            bl2tools.feedback("Delete", "Successfully removed the Object!", 4)
        except ValueError as e:
            bl2tools.feedback("Delete", str(e), 4)

    def copy(self) -> None:
        if self.curr_obj:
            self.clipboard = self.curr_obj
        else:
            self.clipboard = self.objects_by_filter[self.curr_filter][self.object_index]

    @abstractmethod
    def paste(self) -> None:
        pass

    def calculate_preview(self) -> None:
        if self.curr_preview:
            self.curr_preview.destroy()
        if self.curr_filter == "Create" and settings.b_show_preview:
            self.curr_preview = self.objects_by_filter["Create"][self.object_index].get_preview()
        else:
            self.curr_preview = None
        self.delta_time = time()

    @abstractmethod
    def post_render(self, canvas: unrealsdk.UObject, pc: unrealsdk.UObject, offset: int, b_pos_locked: bool) -> None:
        """
        Handle anything related to the canvas, will be called every game tick post render.
        :param b_pos_locked:
        :param offset:
        :param pc:
        :param canvas:
        :return:
        """

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
