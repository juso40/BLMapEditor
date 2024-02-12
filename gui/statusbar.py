from __future__ import annotations

import imgui

from .. import selectedobject as sobj


def draw_statusbar() -> None:
    io = imgui.get_io()
    _x, _y = io.display_size
    window_height = imgui.get_frame_height() + imgui.get_style().window_padding[1]
    imgui.set_next_window_position(0, _y - window_height)
    imgui.set_next_window_size(_x, imgui.get_frame_height())
    imgui.begin(
        "Statusbar",
        flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE |
              imgui.WINDOW_NO_SAVED_SETTINGS | imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_COLLAPSE |
              imgui.WINDOW_NO_FOCUS_ON_APPEARING | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS,
    )
    imgui.same_line()
    imgui.text("Selected Object: ")
    imgui.same_line()
    imgui.text_colored(f"{sobj.SELECTED_OBJECT!s:20.20}", 0.149, 0.533, 0.890, 1.0)
    imgui.same_line()
    imgui.text("| Clipboard: ")
    imgui.same_line()
    imgui.text_colored(f"{sobj.CLIPBOARD!s:20.20}", 0.874, 0.105, 0.933, 1.0)
    imgui.same_line()
    imgui.text("| Active Helper Window: ")
    imgui.same_line()
    imgui.text_colored(f"{sobj.HELPER_INSTANCE!s:20.20}", 1, 0.737, 0.160, 1.0)
    imgui.end()
