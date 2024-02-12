import imgui

from ... import bl2tools, placeables, settings
from ... import selectedobject as sobj


TAG_BUFFER: str = ""


def draw() -> None:
    imgui.push_item_width(-1)
    _draw_metadata()
    imgui.spacing()
    imgui.separator()
    imgui.spacing()
    imgui.spacing()
    imgui.spacing()
    imgui.spacing()
    imgui.pop_item_width()


def _draw_metadata() -> None:
    global TAG_BUFFER  # noqa: PLW0603
    assert sobj.SELECTED_OBJECT is not None
    game_obj: placeables.AbstractPlaceable = sobj.SELECTED_OBJECT
    imgui.text(f"Name: {game_obj.rename if game_obj.rename else game_obj.name}")
    _, game_obj.rename = imgui.input_text("##Name", game_obj.rename, 32)
    if imgui.is_item_hovered():
        imgui.set_tooltip("The name of this object. If left empty, the default name will be used.")

    imgui.spacing()

    imgui.text("Tags:")
    for i, tag in enumerate(game_obj.tags):
        if imgui.button(f"x##{i}"):
            game_obj.tags.remove(tag)
        imgui.same_line()
        imgui.bullet_text(tag)

    if imgui.button("Add##Tag"):
        val_stripped: str = TAG_BUFFER.strip()
        if val_stripped and val_stripped not in game_obj.tags:
            game_obj.tags.append(val_stripped)
        TAG_BUFFER = ""
    imgui.same_line()
    _, TAG_BUFFER = imgui.input_text("##NewTag", TAG_BUFFER, 32)
    if imgui.is_item_hovered():
        imgui.set_tooltip("Tags are used for filtering objects in map loader. Separate tags with a newline.")

    imgui.spacing()

    imgui.text("Metadata:")
    _, game_obj.metadata = imgui.input_text_multiline(
        "##Metadata",
        game_obj.metadata,
        1024,
        -1,
        80,
    )
    if imgui.is_item_hovered():
        imgui.set_tooltip("Metadata is used for storing additional information about this object.")
