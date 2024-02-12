# BLMapEditor
A realtime map editor for Borderlands 2/TPS.  
This editor is a mod for the [UnrealEngine PythonSDK](https://github.com/bl-sdk/PythonSDK).

## Note
This mod is still WIP, do not install this mod and expect to create huge new map layouts or to be crash free.  
If you want to go ahead and mess around with it, but don't expect all your created maps to be working in future updates 
of the editor. As I continue to add features to the editor I may need to rewrite the map loading/saving.  

## Dependencies
This mod depends on [blimgui](https://bl-sdk.github.io/mods/blimgui/) and [coroutines](https://bl-sdk.github.io/mods/Coroutines/) to draw the Editor GUI 
and on [uemath](https://bl-sdk.github.io/mods/UEMathLibrary/) to provide some math functions.

## Controls
Most controls can be rebinded inside the `Modded Keybinds` menu ingame.

F1 to enable the editor/freecam mode. 
Once in editor mode:  
Can be rebinded:
 - F2 to teleport your camera to the selected object
 - F3 to un-/lock the selected objects position
 - F5 to teleport your Pawn to your camera location 
 - Backspace to reset the currently selected objects Position/Scale/Rotation to their default values
 - DEL to destroy the currently selected object
 - P to toggle the object preview on/off

  
## Installation
Download this mod from [here](https://github.com/juso40/BLMapEditor/archive/master.zip).   
Extract all the files from the archive and move them into your games `Win32/Mods/` directory.  
The files should have following structure:
```
└── Win32/
    └── Mods/
         └── MapEditor/
             ├── __init__.py
             ├── bl2tools.py
             ├── canvasutils.py
             ├── editor.py
             ├── settings.py
             ├── undo_redo.py
             ├── Prefabs/*
             ├── Maps/*
             ├── placeablehelper/*
             └── placeables/*
               
```

## Example
I provided a small example in form of a parkour map in the Maps/folder. To load the map travel to "Claptraps Place" and 
open the Editor (by default F1) and scroll to the bottom of the ``Placeables`` window, fill in the Save/Load Name ``parkour`` 
and press ``Load Map``.  
The parkour should then spawn in the games start location.