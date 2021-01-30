# BLMapEditor
A realtime map editor for Borderlands 2/TPS.  
This editor is a mod for the [UnrealEngine PythonSDK](https://github.com/bl-sdk/PythonSDK).

## Note
This mod is still WIP, do not install this mod and expect to create huge new map layouts or to be crash free.  
If you want to go ahead and mess around with it, but don't expect all your created maps to be working in future updates 
of the editor. As I continue to add features to the editor I may need to rewrite the map loading/saving.  


## Controls
Most controls can be rebinded inside the `Modded Keybinds` menu ingame.

F1 to enable the editor/freecam mode. 
Once in editor mode:  
Can be rebinded:
 - F2 to teleport your camera to the selected object
 - F3 to un-/lock the selected objects position
 - F4 to add/remove the currently selected object to/from a prefab
 - F5 to teleport your Pawn to your camera location 
 - Backspace to reset the currently selected objects Position/Scale/Rotation to their default values
 - DEL to destroy the currently selected object
 - 0 to reset the objects distance/offset to your camera     
 - X to cycle trough the available object-Rotation modes 

Cannot be rebinded:
  - LMB to start/stop moving the currently selected object  
  - If moving an object:
    - RMB to cycle trough available object edit modes
    - MouseWheelUp to increase offset/scale/rotation depending on edit mode
    - MouseWheelDown to decrease offset/scale/rotation depending on edit mode
  - If not moving an object:
    - RMB to cycle trough available object list filters
    - MouseWheelUp to move the current object list up
    - MouseWheelDown to move the current object list down
    
## Commands
Because I cannot/won't add a keybind for everything I decided to add a list of new console commands 
that will add some further functionality to the editor.

`mapeditor help` -> show a help message    
`mapeditor speed <int>` -> set the cameras movement speed    
`mapeditor getscale` -> get the current objects scale   
`mapeditor setscale <float>` -> set the objects absolute scale  
`mapeditor offset <int>` -> set the objects offset/distance to your camera  
`mapeditor loadprefab <name>` -> load an existing prefab from your Prefabs/ folder  
`mapeditor saveprefab <name>` -> save your currently selected objects as a new prefab to your Prefabs/ folder  
`mapeditor clearprefab` -> clear all selected objects from your prefab selection  
`mapeditor load <name>` -> load mapchanges for your current map from an existing file inside your Maps/ folder  
`mapeditor save <name>` -> save mapchanges for your current map to a file inside your Maps/ folder  

  
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
             ├── commands.py
             ├── editor.py
             ├── settings.py
             ├── Prefabs/*
             ├── Maps/*
             └── placeables/*
               
```

## Example
I provided a small example in form of a parkour map in the Maps/folder. To load the map travel to "Claptraps Place" and 
use the console command ``mapeditor load parkour``.  
The parkour should then spawn in the games start location.