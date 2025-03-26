"""Driveline
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..common import Vector3


@dataclass
class DrivelinePoint:
    """Driveline points, a cubic hermite spline.

    position
        World position of this point
    direction
        Tangent of this point
    location
        Distance travelled so far along the stage
    """

    position: Vector3
    direction: Vector3
    location: float


@dataclass
class Driveline:
    points: List[DrivelinePoint]

    def compute_length(self, resolution: int = 16) -> float:
        """Compute the driveline length."""
        last_point = None
        length = 0.0
        for point in self.points:
            point.position
            if last_point is not None:
                length += cubic_hermite_segment_length(
                    last_point.position,
                    last_point.direction,
                    point.position,
                    point.direction,
                    resolution,
                )
            last_point = point
        return length


def cubic_hermite_segment_length(
    p0: Vector3,
    d0: Vector3,
    p1: Vector3,
    d1: Vector3,
    resolution: int = 16,
) -> float:
    """Calculate the length of a cubic hermite spline segment.

    p0
        Position of first point
    d0
        Direction (tangent vector) of first point
    p1
        Position of second point
    d1
        Direction (tangent vector) of second point
    resolution
        How many subdivisions to make. More subdivisions gives a more accurate
        length.
    """
    length = 0.0
    last_position = p0
    for i in range(1, resolution + 2):
        relative = i / (resolution + 1)
        position = cubic_hermite_interpolate(p0, d0, p1, d1, relative)
        length += (position - last_position).length()
        last_position = position
    return length


def cubic_hermite_interpolate(
    p0: Vector3,
    d0: Vector3,
    p1: Vector3,
    d1: Vector3,
    x: float,
) -> Vector3:
    """Calculate the position on a cubic hermite segment.

    p0
        Position of first point
    d0
        Direction (tangent vector) of first point
    p1
        Position of second point
    d1
        Direction (tangent vector) of second point
    x
        Relative position along segment, in the range [0, 1]
    """
    x_squared = x * x
    x_cubed = x_squared * x
    a = p0.scale(2 * x_cubed - 3 * x_squared + 1)
    b = d0.scale(x_cubed - 2 * x_squared + x)
    c = p1.scale(-2 * x_cubed + 3 * x_squared)
    d = d1.scale(x_cubed - x_squared)
    return a + b + c + d


def check_segment_is_well_formed(
    A: Vector3,
    a: Vector3,
    B: Vector3,
    b: Vector3,
) -> bool:
    """Given two consecutive points on the driveline:

        A (last_position), a (last_direction)
        B (position), b (direction)

        ^ a
        |  ___------___
        | /            \
        |/              \
        o A              o B
       /                 |\
                         |
                         |
                         v b

    We require the vector formed from a+b points in the direction of AB.
    This is checked by taking a dot product.
    Zero values, i.e. where the two direction vectors are perpendicular
    to the vector AB will cause the game to fail interpolating along the
    curve.
    Negative values - for example where vector a points slightly to the
    left in the diagram, or vector b points slightly to the right - cause
    the game to interpolate the location _backwards_, so if someone drives from
    A to B the game reports the location as if they were driving from B to A.
    As such we reject both of these cases and require the track builder to fix
    them, it will save them a headache down the line.
    """
    result = (a + b).dot(B - A)
    # Reject anything that close to the threshold. Floating point errors
    # can cause "good" (> 0) results, but usually less than 0.01.
    return result > 0.01
