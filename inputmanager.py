from typing import Callable, Dict, List

import unrealsdk  # type: ignore

CALLBACKS: Dict[str, List[Callable[[], None]]] = {}
DEFAULT_INPUTS: list = []


def register_callback(key: str, callback: Callable[[], None]) -> None:
    if key not in CALLBACKS:
        CALLBACKS[key] = []
    CALLBACKS[key].append(callback)


def unregister_callback(key: str, callback: Callable[[], None]) -> None:
    if key not in CALLBACKS:
        return
    CALLBACKS[key].remove(callback)


def input_key(_caller: unrealsdk.UObject, _function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    if params.Event != 0:  # only care for input pressed events
        return True
    for callback in CALLBACKS.get(params.Key, DEFAULT_INPUTS):
        callback()
    return True


def is_key_pressed(key: str) -> bool:
    return key in unrealsdk.GetEngine().GamePlayers[0].Actor.PlayerInput.PressedKeys


unrealsdk.RegisterHook("WillowGame.WillowUIInteraction.InputKey", __file__, input_key)
