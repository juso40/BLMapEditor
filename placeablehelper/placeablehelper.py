from __future__ import annotations
from typing import Tuple, Union, List, Dict, Optional
from abc import ABC, abstractmethod

import unrealsdk
from unrealsdk import *

from .. import placeables
from .. import bl2tools


class PlaceableHelper(ABC):
    def __init__(self, name: str, supported_filters: List[str]):
        self.name: str = name
        self.available_filters: List[str] = supported_filters
        self.objects_by_filter: Dict[str, List[placeables.AbstractPlaceable]] = {f: [] for f in supported_filters}
        self.curr_filter: str = supported_filters[0]
        self.object_index: int = 0
        self.curr_obj: Optional[placeables.AbstractPlaceable] = None

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

    @abstractmethod
    def on_enable(self) -> bool:
        pass

    @abstractmethod
    def on_disable(self) -> bool:
        pass

    def change_filter(self) -> None:
        """
        Change the objects filter.
        :return:
        """

        self.curr_obj = None
        self.curr_filter = self.available_filters[
            (self.available_filters.index(self.curr_filter) + 1) % len(self.available_filters)
            ]

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

    @abstractmethod
    def add_rotation(self, rotator: tuple) -> None:
        """
        Add rotation to the current held object
        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def add_scale(self, scale: float) -> None:
        """
        Add scale to the current held object
        :param scale:
        :return:
        """
        pass

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

    @abstractmethod
    def delete_object(self) -> None:
        """
        Delete the current object.
        :return:
        """
        pass

    @abstractmethod
    def calculate_preview(self) -> None:
        pass

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

    @abstractmethod
    def cleanup(self, mapname: str) -> None:
        """
        Do cleanup, called on every Map Load start.
        :param mapname:
        :return:
        """
        pass

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
