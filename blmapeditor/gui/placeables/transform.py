from imgui_bundle import imgui
from mods_base import get_pc
from uemath import look_at

from ... import placeables, settings
from ... import selectedobject as sobj


def draw() -> None:
    imgui.push_item_width(-1)
    _draw_transform()
    imgui.spacing()
    imgui.separator()
    imgui.spacing()
    imgui.spacing()
    imgui.spacing()
    imgui.spacing()
    imgui.pop_item_width()


def _draw_transform() -> None:
    assert sobj.SELECTED_OBJECT is not None
    game_obj: placeables.AbstractPlaceable = sobj.SELECTED_OBJECT

    imgui.text("Location (X, Y, Z)")
    changed, new_val = imgui.drag_float3("##Location", game_obj.get_location(), max(1, settings.editor_grid_size))
    if changed:
        game_obj.set_location(new_val)
        pc = get_pc()
        look_at(pc, new_val)

    imgui.spacing()

    imgui.text("Scale")
    changed, new_val = imgui.drag_float("##Scale", game_obj.get_scale(), 0.01)
    if changed:
        game_obj.set_scale(new_val)
    imgui.text("Scale3D")
    changed, new_val = imgui.drag_float3("##Scale3D", game_obj.get_scale3d(), 0.01)
    if changed:
        game_obj.set_scale3d(new_val)

    imgui.spacing()

    imgui.text("Rotation (Pitch, Yaw, Roll)")
    changed, new_val = imgui.drag_int3("##Rotation (Pitch, Yaw, Roll)", game_obj.get_rotation(), 128)
    if changed:
        game_obj.set_rotation(new_val)
