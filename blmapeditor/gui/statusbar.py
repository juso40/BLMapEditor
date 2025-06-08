from __future__ import annotations

from imgui_bundle import imgui

from .. import selectedobject as sobj


def draw_statusbar() -> None:
    io = imgui.get_io()
    _x, _y = io.display_size
    window_height = imgui.get_frame_height() + imgui.get_style().window_padding[1]
    imgui.set_next_window_pos((0, _y - window_height))
    imgui.set_next_window_size((_x, imgui.get_frame_height()))
    imgui.begin(
        "Statusbar",
        flags=imgui.WindowFlags_.no_title_bar.value
        | imgui.WindowFlags_.no_resize.value
        | imgui.WindowFlags_.no_move.value
        | imgui.WindowFlags_.no_saved_settings.value
        | imgui.WindowFlags_.no_scrollbar.value
        | imgui.WindowFlags_.no_collapse.value
        | imgui.WindowFlags_.no_focus_on_appearing.value
        | imgui.WindowFlags_.no_docking.value,
    )
    imgui.same_line()
    imgui.text("Selected Object: ")
    imgui.same_line()
    imgui.text_colored((0.149, 0.533, 0.890, 1.0), f"{sobj.SELECTED_OBJECT!s:20.20}")
    imgui.same_line()
    imgui.text("| Clipboard: ")
    imgui.same_line()
    imgui.text_colored((0.874, 0.105, 0.933, 1.0), f"{sobj.CLIPBOARD!s:20.20}")
    imgui.same_line()
    imgui.text("| Active Helper Window: ")
    imgui.same_line()
    imgui.text_colored((1, 0.737, 0.160, 1.0), f"{sobj.HELPER_INSTANCE!s:20.20}")
    imgui.end()
