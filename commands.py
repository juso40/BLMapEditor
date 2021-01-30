import unrealsdk
import functools
from abc import ABC, abstractmethod
from unrealsdk import *

try:
    from Mods.CommandExtensions import RegisterConsoleCommand, UnregisterConsoleCommand
    HAS_CE = True
except ImportError:
    HAS_CE = False

__all__ = ["instance"]


class CommandManager(ABC):
    @abstractmethod
    def enable(self):
        raise NotImplementedError

    @abstractmethod
    def disable(self):
        raise NotImplementedError

    @abstractmethod
    def add_command(self, prefix, fnc):
        raise NotImplementedError


class StandardCommandManager(CommandManager):
    def __init__(self):
        self.prefix_fnc_dict = {}

    def enable(self):
        def command(caller: UObject, function: UFunction, params: FStruct) -> bool:
            fnc = self.prefix_fnc_dict.get(params.Command.split()[0], None)
            if fnc:
                return fnc(params.Command.split(maxsplit=1)[1])
            return True

        unrealsdk.RegisterHook("Engine.PlayerController.ConsoleCommand", __file__, command)

    def disable(self):
        unrealsdk.RemoveHook("Engine.PlayerController.ConsoleCommand", __file__)

    def add_command(self, prefix, fnc):
        self.prefix_fnc_dict[prefix] = fnc


class CECommandManager(CommandManager):
    def __init__(self):
        self.prefix_fnc_dict = {}
        self.is_enabled = False

    @staticmethod
    def _splitter(msg):
        return [x for x in msg.split(" ") if x]

    def _register_command(self, prefix, fnc):
        @functools.wraps(fnc)
        def wrapper(args):
            combined_args = " ".join(args.args)
            if combined_args:
                fnc(" ".join(args.args))
        parser = RegisterConsoleCommand(prefix, wrapper, splitter=self._splitter, add_help=False)
        parser.add_argument("args", nargs="+")

    def enable(self):
        self.is_enabled = True

        for prefix, fnc in self.prefix_fnc_dict.items():
            self._register_command(prefix, fnc)

    def disable(self):
        self.is_enabled = False
        for prefix in self.prefix_fnc_dict:
            UnregisterConsoleCommand(prefix, allow_missing=True)

    def add_command(self, prefix, fnc):
        self.prefix_fnc_dict[prefix] = fnc

        if self.is_enabled:
            self._register_command(prefix, fnc)


instance: CommandManager
if HAS_CE:
    instance = CECommandManager()
else:
    instance = StandardCommandManager()
