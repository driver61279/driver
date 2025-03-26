from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import bpy  # type: ignore
import numpy as np
import math

from rbr_track_formats import errors
from rbr_track_formats.common import NumpyArray
from rbr_track_formats.col.treegen import (
    surface_triangle_dtype,
    surface_triangle_point_dtype,
    build_tree,
)
from rbr_track_formats.col.tree import (
    CollisionTreeRoot,
    BranchTraversal,
)
from rbr_track_formats import dtypes
from rbr_track_formats.mat import (
    MAT,
    ConditionIdentifier,
    SurfaceAge,
    MaterialMap,
)

from rbr_track_formats.logger import Logger
from rbr_track_addon.blender_ops import prepare_objs, TracedObject
from rbr_track_addon.physical_material_editor.properties import RBRMaterialMaps
from rbr_track_addon.shaders.shader_node import VC_SHADOW
from rbr_track_addon.shaders.texture import all_rbr_texture_node_trees_filename
from rbr_track_addon.track_settings import RBRTrackSettings
from rbr_track_addon.util import (
    mesh_vertices_to_loop_positions,
    get_uv_array,
)

from .. import vcol_bake


@dataclass
class RBRMaterialMapsData:
    """RBRMaterialMaps, but not a blender property"""

    position_1: Tuple[float, float]
    position_2: Tuple[float, float]
    repeat_x: bool
    repeat_y: bool

    @staticmethod
    def from_blender(source: RBRMaterialMaps) -> RBRMaterialMapsData:
        (x1, y1) = source.position_1
        (x2, y2) = source.position_2
        return RBRMaterialMapsData(
            position_1=(x1, y1),
            position_2=(x2, y2),
            repeat_x=source.repeat_x,
            repeat_y=source.repeat_y,
        )

    def copy_x(self) -> RBRMaterialMapsData:
        """Make the first half copy in the X direction"""
        return RBRMaterialMapsData(
            position_1=(0.5, self.position_1[1]),
            position_2=(1.5, self.position_2[1]),
            repeat_x=self.repeat_x,
            repeat_y=self.repeat_y,
        )

    def copy_y(self) -> RBRMaterialMapsData:
        """Make the first half copy in the Y direction"""
        return RBRMaterialMapsData(
            position_1=(self.position_1[0], 0.5),
            position_2=(self.position_2[0], 1.5),
            repeat_x=self.repeat_x,
            repeat_y=self.repeat_y,
        )

    def copy_xy(self) -> RBRMaterialMapsData:
        """Make the first half copy in the XY direction"""
        return RBRMaterialMapsData(
            position_1=(0.5, 0.5),
            position_2=(1.5, 1.5),
            repeat_x=self.repeat_x,
            repeat_y=self.repeat_y,
        )

    def area(self) -> float:
        (x1, y1) = self.position_1
        (x2, y2) = self.position_2
        a: float = abs((y2 - y1) * (x2 - x1))
        return a

    def numpy_uvs_to_mat(self, uvs: NumpyArray) -> NumpyArray:
        """uv_to_mat, but operates on dtype=dtypes.uv numpy arrays."""
        (x0, y0) = self.position_1
        (x1, y1) = self.position_2
        dx = x1 - x0
        dy = y1 - y0
        remapped = np.empty(uvs.shape, dtype=dtypes.uv)
        if dx != 0 and x0 > -math.inf:
            remapped["u"] = (uvs["u"] - x0) / dx
        else:
            remapped["u"] = np.zeros(uvs.shape)
        if dy != 0 and y0 > -math.inf:
            remapped["v"] = (uvs["v"] - y0) / dy
        else:
            remapped["v"] = np.zeros(uvs.shape)
        return remapped


def export_physical_materials(
    context: bpy.types.Context,
    stage_name: str = "Blender Addon",
) -> Tuple[Dict[str, List[Tuple[int, RBRMaterialMapsData]]], MAT]:
    """Turn the physical material maps into a MAT file, and a useful structure
    for building the collison mesh.
    """
    track_settings: RBRTrackSettings = context.scene.rbr_track_settings
    surface_types = track_settings.selected_surface_types()
    identifiers = [
        ConditionIdentifier(t, a, stage_name) for t in surface_types for a in SurfaceAge
    ]
    conditions: Dict[ConditionIdentifier, List[MaterialMap]] = dict()
    for ident in identifiers:
        conditions[ident] = []
    # Dictionary from texture name to a list of all the material maps for that
    # texture. The int is the material index in the MAT file.
    textures_oracle: Dict[str, List[Tuple[int, RBRMaterialMapsData]]] = dict()
    idx = 0
    for texture_name, node_tree in all_rbr_texture_node_trees_filename():
        textures_oracle[texture_name] = []
        # This texture might not be a new/normal/worn texture (so use_wear = false).
        # For those textures the addon displays the contents of 'new' to the
        # user for all of new/normal/worn, so we also export the 'new' texture
        # in those cases.
        use_wear = node_tree.nodes["internal"].is_road_surface
        for source_maps in node_tree.nodes["internal"].material_maps:
            source_bitmaps: List[MaterialMap] = [
                m.to_format() for m in source_maps.maps
            ]
            maps_data = RBRMaterialMapsData.from_blender(source_maps)
            material_maps = [(maps_data, source_bitmaps)]
            # We duplicate maps and shift them half way in X and Y. This allows
            # us to cover all triangles which fit in 1/4 of the texture area.
            if source_maps.repeat_x:
                material_maps.append(
                    (maps_data.copy_x(), [m.copy_x() for m in source_bitmaps])
                )
            if source_maps.repeat_y:
                material_maps.append(
                    (maps_data.copy_y(), [m.copy_y() for m in source_bitmaps])
                )
            if source_maps.repeat_x and source_maps.repeat_y:
                material_maps.append(
                    (maps_data.copy_xy(), [m.copy_xy() for m in source_bitmaps])
                )

            for data, bitmaps in material_maps:
                textures_oracle[texture_name].append((idx, data))
                idx += 1
                for ident in conditions:
                    lookup_ident = ident
                    if not use_wear:
                        lookup_ident = ConditionIdentifier(
                            ident.surface_type, SurfaceAge.NEW, ident.name
                        )
                    m = bitmaps[lookup_ident.packed_index()]
                    conditions[ident].append(m)

        # Handle fallback materials.
        # We create infinite maps for the fallback material.
        # Then they are handled (mostly) like normal giant maps, and because
        # they have infinite area they are always last in the stack.
        fallback_materials = node_tree.nodes["internal"].fallback_materials
        fallback_data = RBRMaterialMapsData(
            position_1=(-math.inf, -math.inf),
            position_2=(math.inf, math.inf),
            repeat_x=False,
            repeat_y=False,
        )
        textures_oracle[texture_name].append((idx, fallback_data))
        idx += 1
        for ident in conditions:
            lookup_ident = ident
            if not use_wear:
                lookup_ident = ConditionIdentifier(
                    ident.surface_type, SurfaceAge.NEW, ident.name
                )
            mat = fallback_materials.get_condition(
                lookup_ident.surface_type,
                lookup_ident.surface_age,
            )
            # We can check for undefined materials here, which might be a user
            # error, but this function is not lazy (it exports materials which
            # are unused) so making this an error is annoying.
            # if mat is MaterialID.UNDEFINED:
            conditions[ident].append(MaterialMap.full(mat))
    mat = MAT(conditions=conditions)
    (remapped_mat, remapping) = remap_duplicates(mat)
    for tex in textures_oracle:
        for i, (idx, data) in enumerate(textures_oracle[tex]):
            textures_oracle[tex][i] = (remapping[idx], data)
    return (textures_oracle, remapped_mat)


# This removes duplicate mappings
def remap_duplicates(mat: MAT) -> Tuple[MAT, Dict[int, int]]:
    conditions: Dict[ConditionIdentifier, List[MaterialMap]] = mat.conditions

    num_maps = min([len(l) for l in conditions.values()])

    # Get a dict of (hashes of material maps for the combined set of conditions
    # of that map index) to (source indices with the same hash)
    hashes: Dict[int, Set[int]] = dict()
    for map_idx in range(num_maps):
        these_hashes = dict()
        for ident, maps in conditions.items():
            map = maps[map_idx]
            h = hash(map)
            these_hashes[ident] = h
        h = hash(tuple(these_hashes.items()))
        if h in hashes:
            hashes[h].add(map_idx)
        else:
            hashes[h] = set([map_idx])

    remapping: Dict[int, int] = dict()
    new_conditions: Dict[ConditionIdentifier, List[MaterialMap]] = dict(
        [(ident, []) for ident in conditions]
    )

    for source_indices in hashes.values():
        target_index = min([len(l) for l in new_conditions.values()])
        for source_index in source_indices:
            remapping[source_index] = target_index
        for ident in conditions:
            source_index = min(source_indices)
            new_conditions[ident].append(conditions[ident][source_index])

    new_mat = MAT(conditions=new_conditions)
    return (new_mat, remapping)


def shift_uvs(
    triangle_uv: NumpyArray,  # [ [ dtypes.uv, uv, uv ], ... ]
) -> NumpyArray:
    """Shift UVs towards the texture image area."""

    def stack3(arr: NumpyArray) -> NumpyArray:
        return np.transpose(np.vstack((arr, arr, arr)))

    def shift(
        u: NumpyArray,  # [ [ u, u, u ], ... ]
    ) -> NumpyArray:
        # We try to fit it into the texture area
        # [ [ u, u, u ] ] -> [ [ int, int, int ] ]
        u_div_1 = np.floor_divide(u, 1)
        # [ [ int, int, int ] ] -> [ [ int, int, int ] ]
        u_min_1 = stack3(np.amin(u_div_1, 1))
        u_norm_1 = u_div_1 - u_min_1
        u_mod_1 = np.mod(u, 1)
        return u_norm_1 + u_mod_1

    result = np.empty(triangle_uv.shape, dtypes.uv)
    result["u"] = shift(triangle_uv["u"])
    result["v"] = shift(triangle_uv["v"])
    return result


def fit_map_vectors(
    texture_name: str,
    these_maps: List[Tuple[int, RBRMaterialMapsData]],
    triangle_uv: NumpyArray,  # [ [ dtypes.uv, uv, uv ], ... ]
) -> Tuple[NumpyArray, NumpyArray]:
    """Given the triangle loop UVs for an object, and a bunch of material maps,
    bin each of the UVs into a material map.

    [ [ uv, uv, uv ]         [ map_index
    , [ uv, uv, uv ]    ->   , map_index
    , [ uv, uv, uv ]         , map_index
    ...                      ...
    ]                        ]

    Returns a tuple of (material map IDs, remapped UVs with U-V swapped).
    """
    # Sort so the largest maps are first
    sorted_maps = sorted(these_maps, key=lambda t: t[1].area(), reverse=True)
    # Remap the triangles closer to the texture area
    triangle_uv = shift_uvs(triangle_uv)
    triangle_count = len(triangle_uv)
    # These are the material map IDs for each triangle loop
    binned_tris = np.full(triangle_count, -1, dtype=int)
    remapped_uvs = np.empty((triangle_count, 3), dtype=dtypes.uv)
    # Loop through the maps from largest to smallest, trying to fit UVs into
    # each map.
    for i, material_maps in sorted_maps:
        m: RBRMaterialMapsData = material_maps
        u0 = min(m.position_1[0], m.position_2[0])
        u1 = max(m.position_1[0], m.position_2[0])
        v0 = min(m.position_1[1], m.position_2[1])
        v1 = max(m.position_1[1], m.position_2[1])
        # First we compute which triangle loops fit inside this map in a numpy
        # bool array of shape (-1, 3).
        loops_fit_map = (
            (triangle_uv["u"] >= u0)
            & (triangle_uv["v"] >= v0)
            & (triangle_uv["u"] <= u1)
            & (triangle_uv["v"] <= v1)
        )
        # A triangle might have one point that fits in this map, and two that
        # don't, so we check they all fit by collapsing the second axis with
        # logical and.
        tri_fits_map = np.all(loops_fit_map, axis=1)
        # For the triangles which do entirely fit, we mark them with this map
        # index.
        binned_tris = np.where(
            tri_fits_map,
            np.full(triangle_count, i),
            binned_tris,
        )
        # For the triangles which do entirely fit, we remap the UVs for each
        # loop.
        loop_tri_fits_map = np.vstack(
            (tri_fits_map, tri_fits_map, tri_fits_map)
        ).transpose()
        remapped_uvs = np.where(
            loop_tri_fits_map,
            material_maps.numpy_uvs_to_mat(triangle_uv),
            remapped_uvs,
        )
    # Swap the U and V axis to satisfy RBR.
    u = remapped_uvs["u"].copy()
    v = remapped_uvs["v"].copy()
    remapped_uvs["u"] = v
    remapped_uvs["v"] = u
    if binned_tris.shape != (triangle_count,):
        raise errors.RBRAddonBug(f"bad binned_tris.shape: {binned_tris.shape}")
    if not np.all(binned_tris != -1):
        raise errors.E0107(texture_name=texture_name)
    return (binned_tris, remapped_uvs)


def create_super_triangles(
    logger: Logger,
    material_oracle: Dict[str, List[Tuple[int, RBRMaterialMapsData]]],
    traced_objs: List[TracedObject],
) -> Optional[NumpyArray]:
    """Returns all triangles as surface_triangle_dtype.
    The vertices are baked into the triangle points so we can split easily and
    later compute unique vertex sets.
    """
    per_object_arrays: List[NumpyArray] = []
    for traced_obj in traced_objs:
        mesh = traced_obj.obj.data
        mesh.calc_loop_triangles()
        logger.info(
            f"{traced_obj.source_name()} with {len(mesh.loop_triangles)} triangles"
        )
        material = mesh.materials[0]

        (_, vertices_by_loop) = mesh_vertices_to_loop_positions(
            mesh,
            dtype=dtypes.vector3,
        )

        # One blend value for each loop here
        (shader_node, blending) = vcol_bake.bake_alpha(logger, mesh)

        # get the mesh shading values per loop
        # TODO revisit with shadow baking
        mesh_shading_flat = np.ones(len(mesh.loops) * 4)
        if VC_SHADOW in mesh.attributes:
            mesh.attributes[VC_SHADOW].data.foreach_get("color", mesh_shading_flat)
        mesh_shading = mesh_shading_flat.reshape((-1, 4))[:, 0]

        num_triangles = len(mesh.loop_triangles)
        triangles = np.empty(num_triangles, dtype=surface_triangle_dtype)

        triangle_loops = np.zeros(num_triangles * 3, dtype=int)
        mesh.loop_triangles.foreach_get("loops", triangle_loops)
        (loop_c, loop_b, loop_a) = np.hsplit(
            triangle_loops.reshape((-1, 3)),
            3,
        )

        def get_maps(
            texture: Optional[str],
        ) -> Optional[List[Tuple[int, RBRMaterialMapsData]]]:
            result = None
            if texture is not None and texture != "":
                result = material_oracle.get(texture)
                if result is None:
                    raise errors.RBRAddonBug(
                        f"Colmesh export missing texture '{texture}'"
                    )
            return result

        (diffuse_1, diffuse_1_uv, _uv_velocity_1) = shader_node.walk_to_texture(
            material=material,
            input_name="Diffuse Texture 1",
        )
        diffuse_1_maps = get_maps(diffuse_1)
        if diffuse_1_maps is None:
            raise errors.E0108(material_name=material.name)
        (diffuse_2, diffuse_2_uv, _uv_velocity_2) = shader_node.walk_to_texture(
            material=material,
            input_name="Diffuse Texture 2",
        )
        diffuse_2_maps = get_maps(diffuse_2)

        # UV per loop
        loop_uvs_1 = get_uv_array(
            mesh=mesh,
            layer=diffuse_1_uv,
            invert_v=False,
            material_name=material.name,
        )
        if diffuse_1 is None or loop_uvs_1 is None:
            # We checked this in get_maps
            raise errors.RBRAddonBug("colmesh export: diffuse_1 is None")
        (material_1_id, remapped_uv_1) = fit_map_vectors(
            texture_name=diffuse_1,
            these_maps=diffuse_1_maps,
            triangle_uv=loop_uvs_1[triangle_loops.reshape((-1, 3))],
        )
        triangles["material_1_id"] = material_1_id
        if diffuse_2_maps is not None:
            loop_uvs_2 = get_uv_array(
                mesh=mesh,
                layer=diffuse_2_uv,
                invert_v=False,
                material_name=material.name,
            )
            if diffuse_2 is None or loop_uvs_2 is None:
                # We checked this in get_maps
                raise errors.RBRAddonBug("colmesh export: diffuse_2 is None")
            (material_2_id, remapped_uv_2) = fit_map_vectors(
                texture_name=diffuse_2,
                these_maps=diffuse_2_maps,
                triangle_uv=loop_uvs_2[triangle_loops.reshape((-1, 3))],
            )
            triangles["material_2_id"] = material_2_id
        else:
            remapped_uv_2 = remapped_uv_1
            triangles["material_2_id"] = material_1_id

        def make_point_array(
            loops: NumpyArray, uv_1: NumpyArray, uv_2: NumpyArray
        ) -> NumpyArray:
            arr = np.empty(num_triangles, dtype=surface_triangle_point_dtype)
            arr["position"] = vertices_by_loop[loops]
            arr["blending"] = blending[loops]
            arr["shading"] = mesh_shading[loops]
            arr["material_1_uv"] = uv_1
            arr["material_2_uv"] = uv_2
            return arr

        triangles["a"] = make_point_array(
            loops=loop_a.flatten(),
            uv_1=remapped_uv_1[:, 2],
            uv_2=remapped_uv_2[:, 2],
        )
        triangles["b"] = make_point_array(
            loops=loop_b.flatten(),
            uv_1=remapped_uv_1[:, 1],
            uv_2=remapped_uv_2[:, 1],
        )
        triangles["c"] = make_point_array(
            loops=loop_c.flatten(),
            uv_1=remapped_uv_1[:, 0],
            uv_2=remapped_uv_2[:, 0],
        )

        # TODO fill these in from face maps or something.
        triangles["no_auto_spawn"] = np.full(num_triangles, 1)
        triangles["no_auto_spawn_if_flipped"] = np.full(num_triangles, 1)

        per_object_arrays.append(triangles)

    if len(per_object_arrays) > 0:
        return np.concatenate(per_object_arrays)
    else:
        return None


# This removes material map entries which are not actually used in the colmesh
def remap_unique_materials(
    triangles: NumpyArray,
    mat: MAT,
) -> MAT:
    # Compute material remapping
    unique_mat_ids = np.unique(
        np.concatenate((triangles["material_1_id"], triangles["material_2_id"]))
    )
    # This is a little bit dumb
    num_material_maps = 0
    for condition in mat.conditions:
        material_maps = mat.conditions[condition]
        num_material_maps = len(material_maps)
    # Compute remap array
    remap = np.array([-1] * num_material_maps)
    high_water_mark = 0
    for mat_id in unique_mat_ids:
        remap[mat_id] = high_water_mark
        high_water_mark += 1
    # Remap the triangles
    triangles["material_1_id"] = remap[triangles["material_1_id"]]
    triangles["material_2_id"] = remap[triangles["material_2_id"]]
    # Prune the MAT file
    pruned_mat: Dict[ConditionIdentifier, List[MaterialMap]] = dict()
    for condition in mat.conditions:
        pruned_mat[condition] = []
        for i, material_map in enumerate(mat.conditions[condition]):
            if remap[i] == -1:
                continue
            pruned_mat[condition].append(material_map)
    return MAT(pruned_mat)


def export_world_colmesh(
    logger: Logger,
    traced_objs: List[TracedObject],
    material_oracle: Dict[str, List[Tuple[int, RBRMaterialMapsData]]],
    mat: MAT,
) -> Tuple[
    CollisionTreeRoot, List[Tuple[BranchTraversal, NumpyArray, CollisionTreeRoot]], MAT
]:
    logger.info("Preparing collision mesh objects")
    dupes = prepare_objs(
        logger=logger,
        traced_objs=traced_objs,
        normalise=lambda _: None,
        extra_group=lambda _: None,
    )
    triangles = logger.section(
        "Converting mesh data",
        lambda: create_super_triangles(
            logger=logger,
            material_oracle=material_oracle,
            traced_objs=dupes,
        ),
    )
    if triangles is None:
        raise errors.E0109()

    remapped_mat = remap_unique_materials(triangles, mat)

    (root, subtrees) = logger.section(
        "Building tree",
        lambda: build_tree(logger=logger.info, tris=triangles),
    )

    return (root, subtrees, remapped_mat)
