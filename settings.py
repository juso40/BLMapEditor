from Mods.ModMenu import Options

draw_debug_box_color = Options.Hidden(Caption="Draw Debug Box Color", Description="", StartingValue=[0, 255, 0])

editor_grid_size: int = 0  # 0 = no grid
editor_offset: int = 200  # Distance between the camera and the selected object
editor_filter_range: float = 0  # Filter objects by distance from the camera
sort_by_distance: bool = False  # Sort objects by distance from the camera, will be slow with a lot of objects
b_lock_object_position: bool = False  # Stops the object from being moved by the camera
b_show_preview: bool = False  # Show a preview of the selected object

show_quicksettings_window = Options.Hidden(Caption="Quicksettings", Description="", StartingValue=False)
show_static_meshes_window = Options.Hidden(Caption="Static Meshes", Description="", StartingValue=False)
show_interactive_objects_window = Options.Hidden(
    Caption="Interactive Objects",
    Description="",
    StartingValue=False,
)
show_pawns_window = Options.Hidden(Caption="Pawns", Description="", StartingValue=False)
show_prefabs_window = Options.Hidden(Caption="Prefabs", Description="", StartingValue=False)

ALL_OPTIONS = [
    show_quicksettings_window,
    show_static_meshes_window,
    show_interactive_objects_window,
    show_pawns_window,
    show_prefabs_window,
    draw_debug_box_color,
]
