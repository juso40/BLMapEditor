import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import editor
from . import settings

from ..ModMenu import EnabledSaveType, KeybindManager, ModTypes, SDKMod, SaveModSettings

import imgui
from .. import blimgui

IMGUI_SHOW: bool = False


def _toggle() -> None:
    global IMGUI_SHOW
    if IMGUI_SHOW:
        blimgui.close_window()
        IMGUI_SHOW = False
    else:
        blimgui.create_window("Map Editor")
        blimgui.set_draw_callback(instance.Editor.render)
        IMGUI_SHOW = True


class MapEditor(SDKMod):
    Name = "Map Editor"
    Version = "1.5"
    Types = ModTypes.Utility | ModTypes.Content
    Description = f"Map Editor."
    Author = "Juso"
    SaveEnabledState = EnabledSaveType.NotSaved


    # ToDo: Add functionality back to some keybinds
    # Working from UI only will be too slow
    Keybinds = [KeybindManager.Keybind("Restore Object Defaults", "Backspace"),
                KeybindManager.Keybind("Toggle Editor", "F1"),
                KeybindManager.Keybind("TP To Object", "F2"),
                KeybindManager.Keybind("Lock Obj in Place", "F3"),
                KeybindManager.Keybind("Delete Obj", "Delete"),
                KeybindManager.Keybind("TP my Pawn to me", "F5"),
                KeybindManager.Keybind("Toggle Preview", "P"),
                KeybindManager.Keybind("Toggle Editor Cursor", "Pos1", OnPress=_toggle),
                KeybindManager.Keybind("Cycle Editing Mode", "Tab", IsRebindable=False),
                KeybindManager.Keybind("Stop Editing", "Escape", IsRebindable=False),
                KeybindManager.Keybind("Axis X", "X", IsRebindable=False),
                KeybindManager.Keybind("Axis Y", "Y", IsRebindable=False),
                KeybindManager.Keybind("Axis Z", "Z", IsRebindable=False),
                ]

    def __init__(self):
        self.Editor: editor.Editor = editor.instance
        self.pass_input: bool = False

    def Enable(self) -> None:
        self.pass_input = True

        def end_load(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            level_name: str = bl2tools.get_world_info().GetStreamingPersistentMapName().lower()
            self.Editor.end_loading(level_name)
            return True

        def start_load(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.MovieName is None:
                return True
            self.Editor.start_loading(params.MovieName.lower())
            return True

        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie",
                               __file__,
                               end_load)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientShowLoadingMovie",
                               __file__,
                               start_load)

    def Disable(self) -> None:
        self.pass_input = False

        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie",
                             __file__)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientShowLoadingMovie",
                             __file__)

    def GameInputPressed(self, bind: KeybindManager.Keybind, event: KeybindManager.InputEvent) -> None:
        if self.pass_input and event == KeybindManager.InputEvent.Released:
            self.Editor.game_input_pressed(bind)

    def ModOptionChanged(self, option: unrealsdk.Options.Base, new_value) -> None:
        if option not in self.Options:
            return

        if option.Caption == "Editor Info Color":
            settings.draw_debug_editor_info_color = tuple(new_value)
        elif option.Caption == "Draw Debug Box Color":
            settings.draw_debug_box_color = list(new_value)
        elif option.Caption == "Draw Debug Origin Color":
            settings.draw_debug_origin_color = tuple(new_value)
        elif option.Caption == "Editor Grid Snapsize":
            settings.editor_grid_size = int(new_value)


instance = MapEditor()
unrealsdk.RegisterMod(instance)
