from __future__ import annotations

from imgui_bundle import imgui


def draw_docking_area() -> None:
    io = imgui.get_io()
    _x, _y = io.display_size
    window_height = imgui.get_frame_height() + imgui.get_style().window_padding[1]

    imgui.set_next_window_pos((0, window_height * 2))
    imgui.set_next_window_size((_x, _y - window_height * 3))
    imgui.begin(
        "Docking Area",
        flags=imgui.WindowFlags_.no_title_bar.value
        | imgui.WindowFlags_.no_resize.value
        | imgui.WindowFlags_.no_move.value
        | imgui.WindowFlags_.no_saved_settings.value

        | imgui.WindowFlags_.no_background.value
        | imgui.WindowFlags_.no_decoration.value,
    )

    dockspace_id = imgui.get_id("Docking Area")
    imgui.dock_space(dockspace_id, (0.0, 0.0), imgui.DockNodeFlags_.none.value)

    imgui.end()
