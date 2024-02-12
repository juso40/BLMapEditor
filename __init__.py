import unrealsdk  # type: ignore

from Mods import blimgui
from Mods.ModMenu import EnabledSaveType, KeybindManager, ModTypes, RegisterMod, SDKMod

from . import bl2tools, editor, settings

IMGUI_SHOW: bool = False


def _toggle() -> None:
    global IMGUI_SHOW  # noqa: PLW0603
    if IMGUI_SHOW:
        blimgui.close_window()
        IMGUI_SHOW = False
    else:
        blimgui.create_window("Map Editor")
        blimgui.set_draw_callback(instance.Editor.render)
        IMGUI_SHOW = True


class MapEditor(SDKMod):
    Name = "Map Editor"
    Version = "1.7"
    Types = ModTypes.Utility | ModTypes.Content
    Description = "Map Editor."
    Author = "Juso"
    SaveEnabledState = EnabledSaveType.LoadWithSettings
    Options = settings.ALL_OPTIONS

    # ToDo: Add functionality back to some keybindings
    # Working from UI only will be too slow
    Keybinds = [
        KeybindManager.Keybind("Restore Object Defaults", "Backspace"),
        KeybindManager.Keybind("Toggle Editor", "F1"),
        KeybindManager.Keybind("TP To Object", "F2"),
        KeybindManager.Keybind("Lock Obj in Place", "F3"),
        KeybindManager.Keybind("Delete Obj", "Delete"),
        KeybindManager.Keybind("TP my Pawn to me", "F5"),
        KeybindManager.Keybind("Toggle Preview", "P"),
        KeybindManager.Keybind("Toggle Editor Window", "Home", OnPress=_toggle),
        KeybindManager.Keybind("Cycle Editing Mode", "Tab", IsRebindable=False),
        KeybindManager.Keybind("Axis X", "X", IsRebindable=False),
        KeybindManager.Keybind("Axis Y", "Y", IsRebindable=False),
        KeybindManager.Keybind("Axis Z", "Z", IsRebindable=False),
    ]

    def __init__(self) -> None:
        self.Editor: editor.Editor = editor.instance
        self.pass_input: bool = False

    def Enable(self) -> None:  # noqa: N802
        self.pass_input = True

        def end_load(_caller: unrealsdk.UObject, _function: unrealsdk.UFunction, _params: unrealsdk.FStruct) -> bool:
            level_name: str = bl2tools.get_world_info().GetStreamingPersistentMapName().lower()
            self.Editor.end_loading(level_name)
            return True

        def start_load(_caller: unrealsdk.UObject, _function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.MovieName is None:
                return True
            self.Editor.start_loading(params.MovieName.lower())
            return True

        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", __file__, end_load)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerController.WillowClientShowLoadingMovie", __file__, start_load)

    def Disable(self) -> None:  # noqa: N802
        self.pass_input = False

        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", __file__)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientShowLoadingMovie", __file__)

    def GameInputPressed(self, bind: KeybindManager.Keybind, event: KeybindManager.InputEvent) -> None:  # noqa: N802
        if self.pass_input and event == KeybindManager.InputEvent.Released:
            self.Editor.game_input_pressed(bind)


instance = MapEditor()
RegisterMod(instance)
