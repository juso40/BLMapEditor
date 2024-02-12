from typing import List

from . import placeablehelpers, placeables

# I kinda dislike how I structured this project.
# There should be no reason as to why this file exists, except that it fixes circular imports.
# In the future I definitely should rewrite everything from scratch, but this is a quick fix.

PREFAB_NAME_BUFFER: str = ""

prefab_buffer: List[placeables.AbstractPlaceable] = []


def save_prefab_buffer(name: str) -> None:
    prefab = placeables.Prefab.create_prefab_blueprint(prefab_buffer, name)
    placeablehelpers.PrefabHelper.objects_by_filter["Prefab Blueprints"].append(prefab)
    placeablehelpers.PrefabHelper.objects_by_filter["Prefab Instances"].append(prefab)
    prefab_buffer.clear()
