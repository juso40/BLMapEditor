import unrealsdk
from unrealsdk import *

from math import sin, cos, tan, sqrt

u_rotation_180 = 32768
u_pi = 3.1415926


def rot_to_vec3d(rotation: list):
    f_yaw = rotation[1] * (u_pi / u_rotation_180)
    f_pitch = rotation[0] * (u_pi / u_rotation_180)
    cos_pitch = cos(f_pitch)
    x = cos(f_yaw) * cos_pitch
    y = sin(f_yaw) * cos_pitch
    z = sin(f_pitch)
    return x, y, z


def normalize_vec(vector: iter):
    _len = sqrt(sum(x * x for x in vector))
    return [x / _len for x in vector]


def get_axes(rotation: list):
    x = normalize_vec(rot_to_vec3d(rotation))
    rotation[1] += (u_rotation_180 / 2)  # 90 degree
    r2 = rotation.copy()
    r2[0] = 0
    y = normalize_vec(rot_to_vec3d(r2))
    y[2] = 0
    rotation[1] -= (u_rotation_180 / 2)
    rotation[0] += (u_rotation_180 / 2)
    z = normalize_vec(rot_to_vec3d(rotation))
    return x, y, z


def world_to_screen(canvas, location3d, player_rot, player_loc, player_fov):
    axis_x, axis_y, axis_z = get_axes(player_rot)

    delta = [a - b for a, b in zip(location3d, player_loc)]

    transformed = (sum(a * b for a, b in zip(delta, axis_y)),
                   sum(a * b for a, b in zip(delta, axis_z)),
                   max(1.0, sum(a * b for a, b in zip(delta, axis_x))),
                   )

    fov = player_fov

    screen_center_x = canvas.ClipX / 2
    screen_center_y = canvas.ClipY / 2
    vec_2d_x = screen_center_x + transformed[0] * (screen_center_x / tan(fov * u_pi / 360.0)) / transformed[2]
    vec_2d_y = screen_center_y - transformed[1] * (screen_center_x / tan(fov * u_pi / 360.0)) / transformed[2]
    return vec_2d_x, vec_2d_y


def draw_text(canvas, text, coord_x, coord_y, scale_x, scale_y, color):
    canvas.SetPos(coord_x, coord_y, 0)
    canvas.SetDrawColorStruct(color)
    canvas.DrawText(text, False, scale_x, scale_y, ())


def draw_box(canvas, width, height, coord_x, coord_y, color):
    canvas.SetPos(coord_x, coord_y, 0)
    canvas.SetDrawColorStruct(color)
    canvas.DrawBox(width, height)


def clamp(value, _min, _max):
    return _min if value < _min else _max if value > _max else value


def round_to_multiple(x: float, multiple: float) -> float:
    return multiple * round(x / multiple) if multiple != 0.0 else x
