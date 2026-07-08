from __future__ import annotations

import unrealsdk
from unrealsdk import find_object, logging

loaded_objects: dict[str, list[str]] = {}  # package name -> list of kept alive objects


def _keep_alive(path_name: str, undo: bool = False) -> bool:
    try:
        obj = find_object("Object", path_name)
    except Exception as e:  # noqa: BLE001
        logging.error(f"Error finding object '{path_name}': {e}")
        return False
    if undo:
        obj.ObjectFlags &= ~0x4000
    else:
        obj.ObjectFlags |= 0x4000
    return True


def add_package(name: str) -> None:
    """Add a package to the loaded packages set without loading it yet."""
    if name not in loaded_objects:
        loaded_objects[name] = []
        logging.info(f"Added package to loaded packages: {name}")
    else:
        logging.info(f"Package '{name}' is already loaded.")


def remove_package(name: str) -> None:
    """Remove a package and release all its kept-alive objects."""
    if name in loaded_objects:
        for obj_path in loaded_objects[name]:
            _keep_alive(obj_path, undo=True)
            logging.info(f"Released object: {obj_path}")
        del loaded_objects[name]
        logging.info(f"Removed package: {name}")
    else:
        logging.warning(f"Package '{name}' not found in loaded packages.")


def load_package(name: str) -> bool:
    """Load an Unreal package by name and track it."""
    try:
        unrealsdk.load_package(name)
        logging.info(f"Loaded package: {name}")
        return True
    except Exception as e:  # noqa: BLE001
        logging.error(f"Failed to load package '{name}': {e}")
        return False


def keep_alive(path_name: str, package: str) -> bool:
    """Keep a UObject alive by holding a persistent Python reference."""
    if (objs := loaded_objects.get(package)) and path_name in objs:
        logging.info(f"Object '{path_name}' is already kept alive.")
        return True
    load_package(package)  # Ensure the package is loaded before keeping the object alive
    if not _keep_alive(path_name):
        logging.error(f"Failed to keep object alive: {path_name}")
        return False
    loaded_objects[package].append(path_name)  # Add to the specified package
    logging.info(f"Kept object alive: {path_name}")
    return True


def release_object(path_name: str, package: str) -> None:
    """Release a single kept-alive object, allowing it to be GC'd."""
    if (objs := loaded_objects.get(package)) and path_name in objs:
        _keep_alive(path_name, undo=True)
        objs.remove(path_name)
        logging.info(f"Released object: {path_name}")
    else:
        logging.warning(f"Object '{path_name}' not found in package '{package}'.")


def save_to_json(map_data: dict) -> None:
    """Write the current package/object state into the map JSON dict."""
    if not loaded_objects:
        return
    map_data["LoadedObjects"] = loaded_objects


def load_from_json(map_data: dict) -> None:
    """Restore package loads and kept-alive objects from the map JSON dict."""
    engine_data = map_data.get("LoadedObjects", {})
    for package, objects in engine_data.items():
        if load_package(package):
            for obj_path in objects:
                keep_alive(obj_path, package)
