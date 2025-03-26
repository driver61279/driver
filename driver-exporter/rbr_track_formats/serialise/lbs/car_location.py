from rbr_track_formats.binary import PackBin
from rbr_track_formats.common import Matrix3x3, Matrix4x4
from rbr_track_formats.lbs.car_location import CarLocation

from ..common import vector3_to_binary, matrix4x4_to_binary


def car_location_to_binary(self: CarLocation, bin: PackBin) -> None:
    transformation_matrix: Matrix4x4
    if self.transformation_matrix is None:
        transformation_matrix = Matrix4x4.from_position_and_rotation_matrix(
            position=self.position,
            rotation=Matrix3x3.from_euler_vector(self.euler_vector),
        )
    else:
        transformation_matrix = self.transformation_matrix
    matrix4x4_to_binary(transformation_matrix, bin)
    vector3_to_binary(self.position, bin)
    vector3_to_binary(self.euler_vector, bin)
