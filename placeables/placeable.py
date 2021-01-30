from __future__ import annotations
from typing import Tuple, Union, List
from abc import ABC, abstractmethod

import unrealsdk
from unrealsdk import *


class AbstractPlaceable(ABC):

    def __init__(self, name: str):
        self.name: str = name
        self.b_dynamically_created: bool = False
        self.b_default_attributes: bool = True
        self.is_destroyed: bool = False

    @abstractmethod
    def set_scale(self, scale: float) -> None:
        """
        Set the objects absolute scale.
        :param scale:
        :return:
        """
        pass

    @abstractmethod
    def get_scale(self) -> float:
        """
        Get the objects scale.
        :return:
        """
        pass

    @abstractmethod
    def add_scale(self, scale: float) -> None:
        """
        Increase/decrease the objects absolute scale by a constant value.
        :param scale:
        :return:
        """
        pass

    @abstractmethod
    def set_rotation(self, rotator: iter) -> None:
        """
        Set the objects absolute rotation.
        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def get_rotation(self) -> iter:
        """
        Get the objects current rotation.
        :return:
        """
        pass

    @abstractmethod
    def add_rotation(self, rotator: iter) -> None:
        """
        The given rotator will be added to the current rotation. Pitch += Pitch, Yaw+= Yaw, Roll += Roll
        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def set_location(self, position: iter) -> None:
        """
        Set this objects position to an absolute position.
        :param position: len(position) has to be 3
        :return:
        """
        pass

    @abstractmethod
    def get_location(self) -> iter:
        """
        Get the objects Position in game.
        :return: iter of size 3, real position in game
        """
        pass

    @abstractmethod
    def draw_debug_box(self, player_controller) -> None:
        pass

    @abstractmethod
    def draw_debug_origin(self, canvas, player_controller) -> None:
        pass

    @abstractmethod
    def instantiate(self) -> Tuple[AbstractPlaceable, List[AbstractPlaceable]]:
        """
        If this object holds only a BP for a Placeable Component use this method to instantiate a new object
        associated with the actual in-game components.
        :return: The current object, and an iterator that holds all created objects
        """
        pass

    @abstractmethod
    def holds_object(self, uobject: str) -> bool:
        """
        Check if this Placeable holds the given UObject.
        :param uobject:
        :return: True if this Placeable holds the UObject, else False.
        """
        pass

    @abstractmethod
    def destroy(self) -> List[AbstractPlaceable]:
        """
        If the Object cannot be destroyed, raise an ValueError.
        :return: Returns a list of Placeables to be removed.
        """
        pass

    @abstractmethod
    def store_default_values(self, default_dict: dict) -> None:
        """
        Store the default values for this object. If this Objects Component is not present in the default_dict, add it
        else ignore this call and return.
        :param default_dict:
        :return:
        """
        pass

    @abstractmethod
    def restore_default_values(self, default_dict: dict) -> None:
        """
        Load this objects Components default values from the default_dict.
        :param default_dict:
        :return:
        """
        pass

    @abstractmethod
    def save_to_json(self, saved_json: dict) -> None:
        """
        Every object should decide for itself how/if its saved.
        :param saved_json:
        :return:
        """
        pass
