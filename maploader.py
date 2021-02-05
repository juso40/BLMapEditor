import json
import os
from itertools import cycle
from time import time
from typing import Dict, List, cast

import unrealsdk
from unrealsdk import *

from . import bl2tools
from . import canvasutils
from . import commands
from . import placeables
from . import settings

__all__ = ["instance"]


class MapLoader:

    def __init__(self):
        self.enabled: bool = False

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def start_loading(self, map_name: str) -> None:
        if not self.enabled:
            return

    def end_loading(self, map_name: str) -> None:
        if not self.enabled:
            return



instance = MapLoader()
