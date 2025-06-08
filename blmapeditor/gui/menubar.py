from __future__ import annotations

import pathlib
import webbrowser

from imgui_bundle import imgui

from .. import settings


def callback_save_map(x: str) -> None:
    return print(f"Missing Callback: SAVE_MAP({x})")


def callback_load_map(x: str) -> None:
    return print(f"Missing Callback: LOAD_MAP({x})")


_INPUT_TEXT_SAVE_MODAL: str = "Map Name"
_MAPS_PATH: pathlib.Path = pathlib.Path(__file__).parent.parent / "Maps"
_MAPS_PATH.mkdir(exist_ok=True)


def draw_menu_bar() -> None:  # noqa: PLR0912
    save_modal: bool = False
    load_modal: bool = False
    about_modal: bool = False
    user_guide_modal: bool = False
    if imgui.begin_main_menu_bar():
        if imgui.begin_menu("File"):
            if imgui.menu_item("Save Map", shortcut="Ctrl+S", p_selected=False, enabled=True)[0]:
                save_modal = True
            if imgui.menu_item("Load Map", shortcut="Ctrl+O", p_selected=False, enabled=True)[0]:
                load_modal = True
            imgui.end_menu()
        if imgui.begin_menu("Window"):
            _draw_window_menu_items()
            imgui.end_menu()

        if imgui.begin_menu("Help"):
            if imgui.menu_item("About", shortcut="", p_selected=False, enabled=True)[0]:
                about_modal = True
            elif imgui.menu_item("User Guide", shortcut="", p_selected=False, enabled=True)[0]:
                user_guide_modal = True
            imgui.end_menu()
        imgui.end_main_menu_bar()

    # Save Modal Popup
    if save_modal:
        imgui.open_popup("Save Map")
    if imgui.begin_popup_modal(name="Save Map", flags=imgui.WindowFlags_.always_auto_resize.value)[0]:
        _save_modal()

    # Load Modal Popup
    if load_modal:
        imgui.open_popup("Load Map")
    if imgui.begin_popup_modal(name="Load Map", flags=imgui.WindowFlags_.always_auto_resize.value)[0]:
        _load_modal()

    # About Modal Popup
    if about_modal:
        imgui.open_popup("About")
    if imgui.begin_popup_modal(name="About", flags=imgui.WindowFlags_.always_auto_resize.value)[0]:
        _usage_modal()

    # User Guide Modal Popup
    if user_guide_modal:
        imgui.open_popup("User Guide")
    if imgui.begin_popup_modal(name="User Guide", flags=imgui.WindowFlags_.always_auto_resize.value)[0]:
        _user_guide_modal()


def _draw_window_menu_items() -> None:
    for name, option in [
        ("Settings", settings.show_quicksettings_window),
        ("Static Meshes", settings.show_static_meshes_window),
        ("Interactive Objects", settings.show_interactive_objects_window),
        ("Pawns", settings.show_pawns_window),
        ("Prefabs", settings.show_prefabs_window),
    ]:
        if imgui.menu_item(
            f"{'Hide' if option.value else 'Show'} {name}",
            shortcut="",
            p_selected=False,
            enabled=True,
        )[0]:
            option.value = not option.value


def _save_modal() -> None:
    global _INPUT_TEXT_SAVE_MODAL  # noqa: PLW0603
    imgui.text("Save Current Map to file:")
    _, _INPUT_TEXT_SAVE_MODAL = imgui.input_text("File Name", _INPUT_TEXT_SAVE_MODAL, 32)
    imgui.text(f"Will be saved as '{(_MAPS_PATH / _INPUT_TEXT_SAVE_MODAL).resolve()}.json'")
    imgui.text("Saving this file will overwrite map changes for this streamed level!")

    if imgui.button("Save"):
        callback_save_map(str((_MAPS_PATH / f"{_INPUT_TEXT_SAVE_MODAL}.json").absolute()))
        _INPUT_TEXT_SAVE_MODAL = "Map Name"
        imgui.close_current_popup()
    imgui.same_line()
    if imgui.button("Cancel"):
        _INPUT_TEXT_SAVE_MODAL = "Map Name"
        imgui.close_current_popup()
    imgui.end_popup()


_LOAD_MAP_INDEX: int = -1


def _load_modal() -> None:
    global _LOAD_MAP_INDEX  # noqa: PLW0603
    # List all possible maps from the Maps folder

    maps: list[str] = [_map.name for _map in _MAPS_PATH.glob("*.json")]
    _, _LOAD_MAP_INDEX = imgui.list_box("Maps", _LOAD_MAP_INDEX, maps)
    if imgui.button("Load") and _LOAD_MAP_INDEX != -1:
        callback_load_map(str((_MAPS_PATH / maps[_LOAD_MAP_INDEX]).absolute()))
        _LOAD_MAP_INDEX = -1
        imgui.close_current_popup()

    if imgui.button("Cancel"):
        _LOAD_MAP_INDEX = -1
        imgui.close_current_popup()
    imgui.end_popup()


def _usage_modal() -> None:
    imgui.text_unformatted(
        """
Thank you for using the BLMapEditor!

This mod is very much a work in progress, and is still in its early stages.
While it technically is almost feature complete, it is no where near polished.

Expect bugs, crashes, and other issues. If you find any, please report them on the GitHub page.

If you have any suggestions, or would like to contribute, please feel free to do so!


""",
    )
    if imgui.button("Close"):
        imgui.close_current_popup()
    imgui.same_line()
    if imgui.button("GitHub"):
        webbrowser.open("https://github.com/juso40/BLMapEditor")
    imgui.end_popup()


def _user_guide_modal() -> None:
    imgui.show_user_guide()
    if imgui.button("Close"):
        imgui.close_current_popup()
    imgui.end_popup()
