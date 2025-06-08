from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from unrealsdk import unreal

if TYPE_CHECKING:
    from common import MaterialInterface, Object


class AbstractPlaceable(ABC):
    def __init__(self, name: str, uclass: str) -> None:
        self.uobject_path_name: str = ""
        self.name: str = name
        self.rename: str = ""
        self.metadata: str = ""
        self.tags: list[str] = []
        self.uclass: str = uclass
        self.b_dynamically_created: bool = False
        self.b_default_attributes: bool = True
        self.is_destroyed: bool = False

        self._material_window_open: bool = False

    def __str__(self) -> str:
        return f"{self.rename if self.rename else self.name} ({self.uclass})"

    @abstractmethod
    def get_materials(self) -> list[MaterialInterface]:
        """Get the list of MaterialInstanceConstants this object uses."""
        pass

    @abstractmethod
    def set_materials(self, materials: list[MaterialInterface]) -> None:
        """Set the list of MaterialInstanceConstants for this object."""
        pass

    def add_material(self, material: MaterialInterface) -> None:
        """Add a single MaterialInstanceConstant."""
        materials = self.get_materials()
        materials.append(material)
        self.set_materials(materials)

    def remove_material(self, material: MaterialInterface | None = None, index: int = -1) -> None:
        materials = self.get_materials()
        if material:
            with contextlib.suppress(ValueError):
                materials.remove(material)
        elif index > -1:
            with contextlib.suppress(IndexError):
                materials.pop(index)
        self.set_materials(materials)

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
    def get_scale3d(self) -> list[float]:
        pass

    @abstractmethod
    def set_scale3d(self, scale3d: list[float]) -> None:
        pass

    @abstractmethod
    def set_rotation(self, rotator: list[int] | tuple[int, int, int]) -> None:
        """
        Set the objects absolute rotation.

        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def get_rotation(self) -> list[int]:
        """
        Get the objects current rotation.

        :return: list of 3 ints, Pitch, Yaw, Roll
        """
        pass

    @abstractmethod
    def add_rotation(self, rotator: tuple[int, int, int]) -> None:
        """
        The given rotator will be added to the current rotation. Pitch += Pitch, Yaw+= Yaw, Roll += Roll

        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def set_location(self, position: list[float] | tuple[float, float, float]) -> None:
        """
        Set this objects position to an absolute position.

        :param position: len(position) has to be 3
        :return:
        """
        pass

    @abstractmethod
    def get_location(self) -> list[float]:
        """
        Get the objects Position in game.

        :return: iter of size 3, real position in game
        """
        pass

    @abstractmethod
    def get_bounding_box(self) -> tuple[Object.Vector, Object.Vector]:
        """
        Get the bounding box of this object.

        :return: origin, extent
        """
        pass

    @abstractmethod
    def instantiate(self) -> tuple[AbstractPlaceable, list[AbstractPlaceable]]:
        """
        If this object holds only a BP for a Placeable Component use this method to instantiate a new object
        associated with the actual in-game components.

        :return: The current object, and an iterator that holds all created objects
        """
        pass

    @abstractmethod
    def get_preview(self) -> AbstractPlaceable:
        """
        Return aa previewable version this object. An object returned by this function should have its location
        only be changed using object.Translation

        :return:
        """
        pass

    @abstractmethod
    def set_preview_location(self, location: tuple[float, float, float]) -> None:
        """
        If this object is a preview, use this function to set its location.

        :param location:
        :return:
        """
        pass

    @abstractmethod
    def holds_object(self, uobject: unreal.UObject) -> bool:
        """
        Check if this Placeable holds the given UObject.

        :param uobject:
        :return: True if this Placeable holds the UObject, else False.
        """
        pass

    @abstractmethod
    def destroy(self) -> list[AbstractPlaceable]:
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
