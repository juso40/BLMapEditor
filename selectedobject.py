from math import radians, tan
from typing import TYPE_CHECKING, Optional, Tuple, cast

import unrealsdk  # type: ignore

from Mods.coroutines import Time
from Mods.uemath import Vector, euler_rotate_vector_2d, round_to_multiple
from Mods.uemath.constants import URU_90

from . import prefabbuffer, settings
from .placeables import AbstractPlaceable

if TYPE_CHECKING:
    from .placeablehelpers import PlaceableHelper

HELPER_INSTANCE: Optional["PlaceableHelper"] = None
SELECTED_OBJECT: Optional["AbstractPlaceable"] = None
CURRENT_PREVIEW: Optional["AbstractPlaceable"] = None
CLIPBOARD: Optional["AbstractPlaceable"] = None
CLIPBOARD_HELPER: Optional["PlaceableHelper"] = None


def set_preview(preview: AbstractPlaceable) -> None:
    global CURRENT_PREVIEW  # noqa: PLW0603
    if CURRENT_PREVIEW:
        CURRENT_PREVIEW.destroy()
    CURRENT_PREVIEW = preview


def destroy_preview() -> None:
    global CURRENT_PREVIEW  # noqa: PLW0603
    if CURRENT_PREVIEW:
        cast(AbstractPlaceable, CURRENT_PREVIEW).destroy()
        CURRENT_PREVIEW = None


def add_rotation(rotator: Tuple[int, int, int]) -> None:
    if SELECTED_OBJECT:
        SELECTED_OBJECT.add_rotation(rotator)


def add_scale(scale: float) -> None:
    if SELECTED_OBJECT:
        SELECTED_OBJECT.add_scale(scale)


def calculate_preview() -> None:
    global CURRENT_PREVIEW  # noqa: PLW0602
    if HELPER_INSTANCE:
        HELPER_INSTANCE.update_preview()


def highlight(pc: unrealsdk.UObject, to_highlight: AbstractPlaceable) -> None:
    if not to_highlight:
        return
    pc.FlushPersistentDebugLines()  # Clear previous lines
    pc.DrawDebugBox(*to_highlight.get_bounding_box(), *settings.draw_debug_box_color.CurrentValue, True, 1)
    pc.DrawDebugCoordinateSystem(
        tuple(to_highlight.get_location()),
        tuple(to_highlight.get_rotation()),
        1000,
        True,
        1,
    )


def move_tick(pc: unrealsdk.UObject, offset: float) -> None:
    pc_forward = Vector(pc.CalcViewRotation)
    pc_location = Vector(pc.Location)
    if settings.b_show_preview and CURRENT_PREVIEW:
        _x, _y = euler_rotate_vector_2d(0, 1, pc.CalcViewRotation.Yaw)
        w = tan(radians(pc.ToHFOV(pc.GetFOVAngle()) / 2)) * 200
        _x *= w - 80
        _y *= w - 80
        CURRENT_PREVIEW.set_preview_location(
            (pc_location + 200 * pc_forward - Vector(x=_x, y=_y)).to_tuple(),
        )
        CURRENT_PREVIEW.add_rotation(
            (0, int(URU_90 / 2 * Time.delta_time), 0),
        )

    # highlight the currently selected prefab meshes
    for prefab_data in prefabbuffer.prefab_buffer:
        highlight(pc, prefab_data)

    if SELECTED_OBJECT and not settings.b_lock_object_position:
        forward = pc_forward * offset
        SELECTED_OBJECT.set_location(
            (
                round_to_multiple(pc.Location.X + forward.x, settings.editor_grid_size),
                round_to_multiple(pc.Location.Y + forward.y, settings.editor_grid_size),
                round_to_multiple(pc.Location.Z + forward.z, settings.editor_grid_size),
            )
        )
    # We need to highlight the currently selected object as the last thing, as the object might have moved
    if HELPER_INSTANCE and not SELECTED_OBJECT:
        highlight(pc, HELPER_INSTANCE.get_selected_object())
    elif SELECTED_OBJECT:
        highlight(pc, SELECTED_OBJECT)
