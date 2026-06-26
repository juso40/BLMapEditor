from __future__ import annotations

from imgui_bundle import imgui, icons_fontawesome_4
from unrealsdk import logging

from .. import packagemanager, settings

_PACKAGE_INPUT_BUFFER: str = ""
_OBJECT_INPUT_BUFFER: str = ""


def draw_packages_window() -> None:
    """Draw the Packages & Keep-Alive management window."""
    if not settings.show_packages_window.value:
        return
    _, settings.show_packages_window.value = imgui.begin("Packages", p_open=True)
    _draw_load_package()
    imgui.spacing()
    imgui.separator()
    imgui.spacing()
    for package, objects in packagemanager.loaded_objects.items():
        _draw_kept_alive_objects_section(package, objects)
    imgui.end()


def _draw_load_package() -> None:
    global _PACKAGE_INPUT_BUFFER  # noqa: PLW0603
    imgui.text("Load Package")
    imgui.spacing()

    _, _PACKAGE_INPUT_BUFFER = imgui.input_text("##PackageName", _PACKAGE_INPUT_BUFFER, 64)
    imgui.same_line()
    if imgui.button("Load Package"):
        val_stripped = _PACKAGE_INPUT_BUFFER.strip()
        if val_stripped:
            packagemanager.add_package(val_stripped)
        _PACKAGE_INPUT_BUFFER = ""
    if imgui.is_item_hovered():
        imgui.set_tooltip("Load a package by name (e.g. 'Sanctuary_p').")


def _draw_kept_alive_objects_section(package: str, objects: list[str]) -> None:
    if not imgui.collapsing_header(package):
        return
    global _OBJECT_INPUT_BUFFER  # noqa: PLW0603
    imgui.text("Kept Alive Objects")
    imgui.spacing()

    _, _OBJECT_INPUT_BUFFER = imgui.input_text(f"##ObjectPath{package}", _OBJECT_INPUT_BUFFER, 128)
    imgui.same_line()
    if imgui.button("Keep Alive"):
        val_stripped = _OBJECT_INPUT_BUFFER.strip()
        if val_stripped:
            packagemanager.keep_alive(val_stripped, package)
        _OBJECT_INPUT_BUFFER = ""
    if imgui.is_item_hovered():
        imgui.set_tooltip("Keep an arbitrary UObject alive by full path name.")

    imgui.spacing()

    to_release: str | None = None
    for obj_path in objects:
        if imgui.button(f"{icons_fontawesome_4.ICON_FA_TRASH}##{obj_path}"):
            to_release = obj_path
        imgui.same_line()
        imgui.text(obj_path)

    if to_release:
        packagemanager.release_object(to_release, package)
