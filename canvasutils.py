from typing import List, Tuple, Union

import unrealsdk
from unrealsdk import *

from math import sin, cos, tan, acos, sqrt, atan2, atan

u_rotation_180 = 32768
u_rotation_90 = u_rotation_180 / 2
u_pi = 3.1415926

u_conversion = u_pi / u_rotation_180
u_conversion_back = u_rotation_180 / u_pi


def rot_to_vec3d(rotation: List[int]) -> List[float]:
    """Takes UE3 Rotation as List, returns List of normalized vector."""
    f_yaw = rotation[1] * u_conversion
    f_pitch = rotation[0] * u_conversion
    cos_pitch = cos(f_pitch)
    x = cos(f_yaw) * cos_pitch
    y = sin(f_yaw) * cos_pitch
    z = sin(f_pitch)
    return [x, y, z]


def vec3d_to_rot(vec3d: Union[List[float], Tuple[float, float, float]]) -> List[int]:
    """Obviously wrong, do not use. Get the given Rotator for a normalized Vector."""
    x, y, z = vec3d

    direction = atan2(y, x)

    magnitude = sqrt(x * x + y * y + z * z)

    yaw = magnitude * cos(direction) * u_conversion_back
    pitch = magnitude * sin(direction) * u_conversion_back

    return [pitch, yaw, 0]


def normalize_vec(vector: Union[List[float], Tuple[float, float, float]]) -> List[float]:
    _len = sqrt(sum(x * x for x in vector))
    return [x / _len for x in vector]


def get_axes(rotation: List[int]) -> Tuple[List[float], List[float], List[float]]:
    x = rot_to_vec3d(rotation)
    rotation[1] += u_rotation_90
    r2 = rotation.copy()
    r2[0] = 0
    y = rot_to_vec3d(r2)
    y[2] = 0
    rotation[1] -= u_rotation_90
    rotation[0] += u_rotation_90
    z = rot_to_vec3d(rotation)
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


def draw_text(canvas: unrealsdk.UObject,
              text: str,
              coord_x: int,
              coord_y: int,
              scale_x: float,
              scale_y: float,
              color: Tuple[int, int, int, int]) -> None:
    canvas.SetPos(coord_x, coord_y, 0)
    canvas.SetDrawColorStruct(color)
    canvas.DrawText(text, False, scale_x, scale_y, ())


def draw_box(canvas: unrealsdk.UObject,
             width: float,
             height: float,
             coord_x: int,
             coord_y: int,
             color: Tuple[int, int, int, int]) -> None:
    canvas.SetPos(coord_x, coord_y, 0)
    canvas.SetDrawColorStruct(color)
    canvas.DrawBox(width, height)


def clamp(value: float, _min: float, _max: float) -> float:
    return _min if value < _min else _max if value > _max else value


def round_to_multiple(x: float, multiple: float) -> float:
    return multiple * round(x / multiple) if multiple != 0.0 else x


def euler_rotate_vector_2d(x: float, y: float, angle: float) -> Tuple[float, float]:
    angle = angle * u_conversion
    s = sin(angle)
    c = cos(angle)
    x_r = x * c - y * s
    y_r = x * s + y * c
    return x_r, y_r


def rotate_to_location(loc_from: List[float], loc_to: List[float]) -> List[int]:
    xa, ya, za = loc_from
    xb, yb, zb = loc_to
    xd, yd, zd = xa - xb, ya - yb, za - zb  # delta
    hyp = sqrt(xd * xd + yd * yd)

    pitch = -int(atan(zd / hyp) * u_conversion_back)
    yaw = int(atan(yd / xd) * u_conversion_back)
    roll = 0

    if xd >= 0:
        yaw += u_rotation_180

    # clamp
    while yaw < -u_rotation_180:
        yaw += (2 * u_rotation_180)
    while yaw > u_rotation_180:
        yaw -= (2 * u_rotation_180)

    return [pitch, yaw, roll]


def rotate_location(rotator: List[int], location: List[float]) -> List[float]:
    pitch, yaw, roll = [x * u_conversion for x in rotator]
    cosa = cos(yaw)
    sina = sin(yaw)

    cosb = cos(pitch)
    sinb = sin(pitch)

    cosc = cos(roll)
    sinc = sin(roll)

    Axx = cosa * cosb
    Axy = cosa * sinb * sinc - sina * cosc
    Axz = cosa * sinb * cosc + sina * sinc
    Ayx = sina * cosb
    Ayy = sina * sinb * sinc + cosa * cosc
    Ayz = sina * sinb * cosc - cosa * sinc
    Azx = -sinb
    Azy = cosb * sinc
    Azz = cosb * cosc

    px, py, pz = location
    return [Axx * px + Axy * py + Axz * pz,
            Ayx * px + Ayy * py + Ayz * pz,
            Azx * px + Azy * py + Azz * pz]


def dot_product(vec_a: Union[List[float], Tuple[float, float, float]],
                vec_b: Union[List[float], Tuple[float, float, float]],
                ignore_z: bool = True) -> Tuple[float, float, float]:
    """Get the dot product of 2 normalized vectors."""

    xa, ya, za = vec_a
    xb, yb, zb = vec_b

    return (xa * xb + ya * yb) if ignore_z else (xa * xb + ya * yb + za * zb)
