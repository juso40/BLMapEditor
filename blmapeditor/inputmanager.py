from collections.abc import Callable
from typing import Any

from mods_base import ENGINE
from mods_base.keybinds import EInputEvent
from unrealsdk import hooks, unreal

CALLBACKS: dict[str, list[Callable[[], None]]] = {}
DEFAULT_INPUTS: list = []


def register_callback(key: str, callback: Callable[[], None]) -> None:
    if key not in CALLBACKS:
        CALLBACKS[key] = []
    CALLBACKS[key].append(callback)


def unregister_callback(key: str, callback: Callable[[], None]) -> None:
    if key not in CALLBACKS:
        return
    CALLBACKS[key].remove(callback)


def input_key(_obj: unreal.UObject, args: unreal.WrappedStruct, _ret: Any, _func: unreal.BoundFunction) -> None:
    if args.Event != EInputEvent.IE_Pressed:  # only care for input pressed events
        return
    for callback in CALLBACKS.get(args.Key, DEFAULT_INPUTS):
        callback()


def is_key_pressed(key: str) -> bool:
    return key in ENGINE.GamePlayers[0].Actor.PlayerInput.PressedKeys


hooks.add_hook("WillowGame.WillowUIInteraction:InputKey", hooks.Type.PRE, __file__, input_key)
