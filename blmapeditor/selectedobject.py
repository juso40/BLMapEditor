from __future__ import annotations

from math import radians, tan
from typing import TYPE_CHECKING, cast

from coroutines import Time
from uemath import Rotator, Vector, euler_rotate_vector_2d, round_to_multiple
from uemath.constants import URU_90

from . import prefabbuffer, settings
from .placeables import AbstractPlaceable

if TYPE_CHECKING:
    from common import WillowPlayerController

    from .placeablehelpers import PlaceableHelper

HELPER_INSTANCE: PlaceableHelper | None = None
SELECTED_OBJECT: AbstractPlaceable | None = None
CURRENT_PREVIEW: AbstractPlaceable | None = None
CLIPBOARD: AbstractPlaceable | None = None
CLIPBOARD_HELPER: PlaceableHelper | None = None


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


def add_rotation(rotator: tuple[int, int, int]) -> None:
    if SELECTED_OBJECT:
        SELECTED_OBJECT.add_rotation(rotator)


def add_scale(scale: float) -> None:
    if SELECTED_OBJECT:
        SELECTED_OBJECT.add_scale(scale)


def calculate_preview() -> None:
    global CURRENT_PREVIEW  # noqa: PLW0602
    if HELPER_INSTANCE:
        HELPER_INSTANCE.update_preview()


def highlight(pc: WillowPlayerController, to_highlight: AbstractPlaceable | None) -> None:
    if not to_highlight:
        return
    pc.FlushPersistentDebugLines()  # Clear previous lines
    r, g, b = settings.draw_debug_box_color.value
    pc.DrawDebugBox(*to_highlight.get_bounding_box(), R=r, G=g, B=b, bPersistentLines=True, Lifetime=1)
    pc.DrawDebugCoordinateSystem(
        Vector(to_highlight.get_location()).to_ue_vector(),
        Rotator(to_highlight.get_rotation()).to_ue_rotator(),
        1000,
        True,
        1,
    )


def move_tick(pc: WillowPlayerController, offset: float) -> None:
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
            ),
        )
    # We need to highlight the currently selected object as the last thing, as the object might have moved
    if HELPER_INSTANCE and not SELECTED_OBJECT:
        highlight(pc, HELPER_INSTANCE.get_selected_object())
    elif SELECTED_OBJECT:
        highlight(pc, SELECTED_OBJECT)
