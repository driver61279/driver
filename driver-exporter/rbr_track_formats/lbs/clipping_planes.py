"""Clipping planes are large walls which help optimisation of a stage. They are
not visible in game, but objects behind them are not drawn.
"""

from __future__ import annotations
from dataclasses import dataclass

from ..common import NumpyArray


@dataclass
class ClippingPlanes:
    """ClippingPlanes provides a method of performance optimisation.
    Geometry defined here will hide any visible geometry behind it.
    omnidirectional_planes will hide anything behind them when viewed from any
    direction, but directional_planes will only hide things behind them when
    the triangles are viewed from the clockwise-wound direction. They share
    vertices.
    """

    directional_planes: NumpyArray
    omnidirectional_planes: NumpyArray
    vertices: NumpyArray
