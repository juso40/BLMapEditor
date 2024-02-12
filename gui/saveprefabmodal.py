import imgui

from .. import prefabbuffer as pb

SHOW_SAVE_PREFAB_MODAL: bool = False


def draw_save_prefab_modal() -> None:
    global SHOW_SAVE_PREFAB_MODAL  # noqa: PLW0603
    SHOW_SAVE_PREFAB_MODAL = True
    imgui.open_popup("Save Prefab")
    _modal()


def try_show_save_prefab_modal() -> None:
    if SHOW_SAVE_PREFAB_MODAL:
        imgui.open_popup("Save Prefab")
        _modal()


def _modal() -> None:
    global SHOW_SAVE_PREFAB_MODAL  # noqa: PLW0603
    if imgui.begin_popup_modal(title="Save Prefab", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
        imgui.text("Enter a name for the prefab")
        in_text = imgui.input_text("##prefab_name", pb.PREFAB_NAME_BUFFER, 32)
        if in_text[0]:
            pb.PREFAB_NAME_BUFFER = in_text[1]
        if imgui.button("Save"):
            pb.save_prefab_buffer(pb.PREFAB_NAME_BUFFER)
            SHOW_SAVE_PREFAB_MODAL = False
            imgui.close_current_popup()
        imgui.same_line()
        if imgui.button("Cancel"):
            imgui.close_current_popup()
            SHOW_SAVE_PREFAB_MODAL = False
        imgui.end_popup()
