from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple, Union

import unrealsdk
from unrealsdk import *

from .. import bl2tools
from .. import canvasutils
from .. import settings

from ...PyImgui import pyd_imgui

_material_instances: List[unrealsdk.UObject] = []
_material_instances_filtered: List[unrealsdk.UObject] = []
_material_instances_filtered_names: List[str] = []


class AbstractPlaceable(ABC):

    def __init__(self, name: str, uclass: str):
        self.name: str = name
        self.uclass: str = uclass
        self.b_dynamically_created: bool = False
        self.b_default_attributes: bool = True
        self.material_int: int = -1
        self.new_material_int: int = -1
        self.material_filter: str = ""
        self.is_destroyed: bool = False

        self._material_window_open: bool = False

    @abstractmethod
    def get_materials(self) -> List[unrealsdk.UObject]:
        """Get the list of MaterialInstanceConstants this object uses."""
        pass

    @abstractmethod
    def set_materials(self, materials: List[unrealsdk.UObject]) -> None:
        """Set the list of MaterialInstanceConstants for this object."""

    def add_material(self, material: unrealsdk.UObject) -> None:
        """Add a single MaterialInstanceConstant."""
        materials = self.get_materials()
        materials.append(material)
        self.set_materials(materials)

    def remove_material(self, material: unrealsdk.UObject = None, index: int = -1) -> None:
        materials = self.get_materials()
        if material:
            try:
                materials.remove(material)
            except ValueError:
                pass
        elif index > -1:
            try:
                materials.pop(index)
            except IndexError:
                pass
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
    def get_scale3d(self) -> List[float]:
        pass

    def set_scale3d(self, scale3d: List[float]) -> None:
        pass

    @abstractmethod
    def set_rotation(self, rotator: Union[List[int], Tuple[int, int, int]]) -> None:
        """
        Set the objects absolute rotation.
        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def get_rotation(self) -> List[int]:
        """
        Get the objects current rotation.
        :return:
        """
        pass

    @abstractmethod
    def add_rotation(self, rotator: Tuple[int, int, int]) -> None:
        """
        The given rotator will be added to the current rotation. Pitch += Pitch, Yaw+= Yaw, Roll += Roll
        :param rotator:
        :return:
        """
        pass

    @abstractmethod
    def set_location(self, position: Union[List[float], Tuple[float, float, float]]) -> None:
        """
        Set this objects position to an absolute position.
        :param position: len(position) has to be 3
        :return:
        """
        pass

    @abstractmethod
    def get_location(self) -> List[float]:
        """
        Get the objects Position in game.
        :return: iter of size 3, real position in game
        """
        pass

    @abstractmethod
    def draw_debug_box(self, player_controller: unrealsdk.UObject) -> None:
        pass

    @abstractmethod
    def draw_debug_origin(self, canvas: unrealsdk.UObject, player_controller: unrealsdk.UObject) -> None:
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
    def get_preview(self) -> AbstractPlaceable:
        """
        Return aa previewable version this object. An object returned by this function should have its location
        only be changed using object.Translation
        :return:
        """
        pass

    @abstractmethod
    def set_preview_location(self, location: Tuple[float, float, float]) -> None:
        """
        If this object is a preview, use this function to set its location.
        :param location:
        :return:
        """
        pass

    @abstractmethod
    def holds_object(self, uobject: unrealsdk.UObject) -> bool:
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

    @abstractmethod
    def draw(self) -> None:
        pyd_imgui.push_item_width(-1)

        pyd_imgui.text("Location (X, Y, Z)")
        dragged_loc = pyd_imgui.drag_float3("##Location", self.get_location(), max(1, settings.editor_grid_size))
        if dragged_loc[0]:
            self.set_location(dragged_loc[1])
            pc = bl2tools.get_player_controller()
            pc.Rotation = tuple(canvasutils.rotate_to_location([pc.Location.X,
                                                                pc.Location.Y,
                                                                pc.Location.Z],
                                                               dragged_loc[1]))
        pyd_imgui.spacing()

        pyd_imgui.text("Scale")
        dragged_scale = pyd_imgui.drag_float("##Scale", self.get_scale(), 0.01)
        if dragged_scale[0]:
            self.set_scale(dragged_scale[1])

        pyd_imgui.text("Scale3D")
        dragged_scale3d = pyd_imgui.drag_float3("##Scale3D", self.get_scale3d(), 0.01)
        if dragged_scale3d[0]:
            self.set_scale3d(dragged_scale3d[1])

        pyd_imgui.separator()

        pyd_imgui.text("Rotation (Pitch, Yaw, Roll)")
        dragged_rotation = pyd_imgui.drag_int3("##Rotation (Pitch, Yaw, Roll)", self.get_rotation(), 100)
        if dragged_rotation[0]:
            self.set_rotation(dragged_rotation[1])

        pyd_imgui.spacing()

        ################################################################################################################
        # Begin Material Helper Window                                                                                 #
        ################################################################################################################
        if pyd_imgui.button("Add Material"):
            self._material_window_open = True
            _material_instances.extend(unrealsdk.FindAll("MaterialInstanceConstant")[1:])

        if self._material_window_open:
            global _material_instances_filtered, _material_instances_filtered_names
            pyd_imgui.begin("MaterialWindow")
            b_filtered, self.material_filter = pyd_imgui.input_text("Filter Materials", self.material_filter, 24)
            if b_filtered:
                _material_instances_filtered = [x for x in _material_instances
                                                if self.material_filter.lower()
                                                in bl2tools.get_obj_path_name(x).lower()]
                _material_instances_filtered_names = [bl2tools.get_obj_path_name(x)
                                                      for x in _material_instances_filtered]

            self.new_material_int = pyd_imgui.list_box("##Materials",
                                                       self.new_material_int,
                                                       _material_instances_filtered_names)[1]

            if pyd_imgui.button("Add Material"):
                self.add_material(_material_instances_filtered[self.new_material_int])
            if pyd_imgui.button("Remove Material"):
                self.remove_material(material=_material_instances_filtered[self.new_material_int])
            if pyd_imgui.button("Close"):
                self._material_window_open = False
                _material_instances.clear()
                _material_instances_filtered.clear()
            pyd_imgui.end()
        ################################################################################################################
        pyd_imgui.same_line()
        if pyd_imgui.button("Remove Material"):
            self.remove_material(index=self.material_int)
        pyd_imgui.text("Materials")
        self.material_int = pyd_imgui.list_box("##Materials",
                                               self.material_int,
                                               [bl2tools.get_obj_path_name(x) for x in self.get_materials()])[1]

        pyd_imgui.pop_item_width()
