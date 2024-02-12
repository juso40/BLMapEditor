from typing import Callable

import imgui
import unrealsdk  # type: ignore

from Mods.ModMenu import SaveAllModSettings

from .. import bl2tools, settings

CALLBACK_CHECKBOX_SHOW_PREVIEW: Callable[[bool], None] = lambda x: unrealsdk.Log(
    f"Missing Callback: CHECKBOX_SHOW_PREVIEW({x})",
)


def draw_settings_menu() -> None:
    """
    Draw the Settings UI Window. Populated with various Editor Specific values.
    Most settings will be saved using the SDK SaveModSettings() function.

    :return:
    """
    if not settings.show_quicksettings_window.CurrentValue:
        return
    _, settings.show_quicksettings_window.CurrentValue = imgui.begin("Settings", closable=True)
    _populate_settings_menu()
    imgui.end()


def _populate_settings_menu() -> None:
    """Populate the Settings Menu with all gui elements."""

    # Draw two checkboxes, one for Locking the object position, and one for showing a preview of the object.
    _, settings.b_lock_object_position = imgui.checkbox("Lock Object Position", settings.b_lock_object_position)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Stops the object from being moved by the camera.")
    imgui.same_line()
    pressed, settings.b_show_preview = imgui.checkbox("Show Preview", settings.b_show_preview)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Show a preview of the selected object.")
    if pressed:  # check if it is pressed this frame, to avoid spamming the preview calculation
        CALLBACK_CHECKBOX_SHOW_PREVIEW(settings.b_show_preview)
    imgui.same_line()
    _, settings.sort_by_distance = imgui.checkbox("Live Sort by Distance", settings.sort_by_distance)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Sort objects by distance from the camera, updates every 2 seconds for performance reasons.")

    # Draw Float Sliders for the Camera Speed, Camera-Object Distance, and Grid Size.
    pc = bl2tools.get_player_controller()
    _, pc.SpectatorCameraSpeed = imgui.slider_float("Camera-Speed", pc.SpectatorCameraSpeed, 0, 20000)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Camera Movement Speed.")

    _, settings.editor_offset = imgui.slider_float("Camera-Object Distance", settings.editor_offset, 0, 2000)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Distance between the camera and the selected object.")

    _, settings.editor_grid_size = imgui.slider_float("Grid Size", settings.editor_grid_size, 0, 500)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Snap objects to a 'grid'. 0 = no grid.")

    _, settings.editor_filter_range = imgui.slider_float("Range Filter", settings.editor_filter_range, 0, 200)
    if imgui.is_item_hovered():
        imgui.set_tooltip(
            "Filter objects by distance from the camera. 0=Unlimited. Distance in meters."
            " You may need to press the 'Refresh' button to see changes.",
        )

    color_changed, new_col = imgui.color_edit3(
        "Debug Box Color",
        *[x / 255 for x in settings.draw_debug_box_color.CurrentValue],
        imgui.COLOR_EDIT_PICKER_HUE_BAR,
    )
    if imgui.is_item_hovered():
        imgui.set_tooltip("Change the color of the debug box around the selected object.")
    if color_changed:
        settings.draw_debug_box_color.CurrentValue = [int(x * 255) for x in new_col]
        SaveAllModSettings()
