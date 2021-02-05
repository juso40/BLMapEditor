import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import commands
from . import editor
from . import maploader
from . import settings
from ..ModMenu import EnabledSaveType, KeybindManager, ModTypes, Options, SDKMod


class MapEditor(SDKMod):
    Name = "Map Editor"
    Version = "0.9 Not so janky beta"
    Types = ModTypes.Utility | ModTypes.Content
    Description = f"Map Editor WIP.\n\n{Version}"
    Author = "Juso"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [Options.Slider("Editor Info Color.R", "Change the color for the info inside the Editor",
                              102, 0, 255, 1),
               Options.Slider("Editor Info Color.G", "Change the color for the info inside the Editor",
                              104, 0, 255, 1),
               Options.Slider("Editor Info Color.B", "Change the color for the info inside the Editor",
                              112, 0, 255, 1),
               Options.Slider("Editor Info Scale", "Change the scale for the info inside the Editor",
                              100, 100, 500, 1),
               Options.Slider("Draw Debug Origin Color.R",
                              "Change the color for the debug origin inside the Editor",
                              244, 0, 255, 1),
               Options.Slider("Draw Debug Origin Color.G",
                              "Change the color for the debug origin inside the Editor",
                              64, 0, 255, 1),
               Options.Slider("Draw Debug Origin Color.B",
                              "Change the color for the debug origin inside the Editor",
                              177, 0, 255, 1),
               Options.Slider("Draw Debug Box Color.R", "Change the color for the debug box inside the Editor",
                              0, 0, 255, 1),
               Options.Slider("Draw Debug Box Color.G", "Change the color for the debug box inside the Editor",
                              255, 0, 255, 1),
               Options.Slider("Draw Debug Box Color.B", "Change the color for the debug box inside the Editor",
                              0, 0, 255, 1)
               ]

    Keybinds = [KeybindManager.Keybind("Restore Object Defaults", "Backspace"),
                KeybindManager.Keybind("TP To Object", "F2"),
                KeybindManager.Keybind("Lock Obj in Place", "F3"),
                KeybindManager.Keybind("Delete Obj", "Delete"),
                KeybindManager.Keybind("Toggle Editor", "F1"),
                KeybindManager.Keybind("Editor Offset Reset", "0"),
                KeybindManager.Keybind("Cycle Pitch|Yaw|Roll", "X"),
                KeybindManager.Keybind("Add/Remove to/from Prefab", "F4"),
                KeybindManager.Keybind("TP my Pawn to me", "F5"),
                KeybindManager.Keybind("Toggle Preview", "P"),
                KeybindManager.Keybind("Change Editor Mode", "U")
                ]

    def __init__(self):
        self.Editor = editor.instance
        self.MapLoader = maploader.instance
        self.pass_input = False

    def Enable(self) -> None:
        self.pass_input = True
        commands.instance.enable()

        def end_load(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            self.Editor.end_loading(bl2tools.get_world_info().GetStreamingPersistentMapName().lower())
            self.MapLoader.end_loading(bl2tools.get_world_info().GetStreamingPersistentMapName().lower())
            return True

        def start_load(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.MovieName is None:
                return True
            self.Editor.start_loading(params.MovieName.lower())
            self.MapLoader.start_loading(params.MovieName.lower())
            return True

        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie",
                               "hkManagerEndLoading",
                               end_load)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientShowLoadingMovie",
                               "hkManagerStartLoading",
                               start_load)

    def Disable(self) -> None:
        self.pass_input = False
        commands.instance.disable()

        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie",
                             __file__)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientShowLoadingMovie",
                             __file__)

    def GameInputPressed(self, bind) -> None:
        if self.pass_input:
            self.Editor.game_input_pressed(bind)

    def ModOptionChanged(self, option: unrealsdk.Options.Base, new_value) -> None:
        if option not in self.Options:
            return

        if option.Caption == "Editor Info Color.R":
            x = list(settings.draw_debug_editor_info_color)
            x[2] = int(new_value)
            settings.draw_debug_editor_info_color = tuple(x)
        elif option.Caption == "Editor Info Color.G":
            x = list(settings.draw_debug_editor_info_color)
            x[1] = int(new_value)
            settings.draw_debug_editor_info_color = tuple(x)
        elif option.Caption == "Editor Info Color.B":
            x = list(settings.draw_debug_editor_info_color)
            x[0] = int(new_value)
            settings.draw_debug_editor_info_color = tuple(x)
        elif option.Caption == "Editor Info Scale":
            settings.draw_debug_editor_info_scale = new_value / 100
        elif option.Caption == "Draw Debug Box Color.R":
            settings.draw_debug_box_color[0] = int(new_value)
        elif option.Caption == "Draw Debug Box Color.G":
            settings.draw_debug_box_color[1] = int(new_value)
        elif option.Caption == "Draw Debug Box Color.B":
            settings.draw_debug_box_color[2] = int(new_value)
        elif option.Caption == "Draw Debug Origin Color.R":
            x = list(settings.draw_debug_origin_color)
            x[2] = int(new_value)
            settings.draw_debug_origin_color = tuple(x)
        elif option.Caption == "Draw Debug Origin Color.G":
            x = list(settings.draw_debug_origin_color)
            x[1] = int(new_value)
            settings.draw_debug_origin_color = tuple(x)
        elif option.Caption == "Draw Debug Origin Color.B":
            x = list(settings.draw_debug_origin_color)
            x[0] = int(new_value)
            settings.draw_debug_origin_color = tuple(x)


unrealsdk.RegisterMod(MapEditor())
