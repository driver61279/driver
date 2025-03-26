from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy.lib.recfunctions import (
    structured_to_unstructured,
    unstructured_to_structured,
)

from rbr_track_formats.common import (
    AaBbBoundingBox,
    NumpyArray,
    NumpyDType,
    Vector3,
    compute_bounding_box_from_positions,
)
from rbr_track_formats.lbs.geom_blocks import (
    GeomBlock,
    RenderChunkDistance,
    TransformedRenderChunkData,
)
from rbr_track_formats.lbs.object_blocks import (
    ObjectBlock,
    ObjectBlockLOD,
    ObjectBlockSegment,
)
from rbr_track_formats.lbs.visible_object_vecs import VisibleObjectVec
from rbr_track_formats import dtypes, errors
from rbr_track_formats.lbs import WorldChunk
from rbr_track_formats.logger import Logger


def split_array_by(arr: NumpyArray, cond: NumpyArray) -> Tuple[NumpyArray, NumpyArray]:
    return (arr[cond], arr[~cond])


# @dataclass
# class Bin:
#    x: int
#    y: int
#
#    def __lt__(self, other) -> bool:  # type: ignore
#        return (self.x, self.y).__lt__((other.x, other.y))
#
#    def __hash__(self) -> int:
#        return (self.x, self.y).__hash__()


Bin = Any  # TODO


def split_by_chunk_size(
    chunk: TransformedRenderChunkData,
    chunk_size: float,
) -> Dict[Bin, TransformedRenderChunkData]:
    x = chunk.vertices["position"]["x"]
    z = chunk.vertices["position"]["z"]
    # These are already converted to RBR coords, hence x, z not x, y
    xz = np.vstack((x, z)).transpose()
    abc = chunk.triangles
    # Create a 3D array:
    # [ [ [x z] [x z] [x z] ]
    # , [ [x z] [x z] [x z] ]
    # ... one for each triangle
    # ]
    triangle_verts = np.take(xz, abc, axis=0)
    # Collapse it to a 2D array of average position (triangle centre)
    # [ [x z]
    # , [x z]
    # ... one for each triangle
    # ]
    triangle_centres = np.average(triangle_verts, axis=1)
    # Convert the centres into bins
    # [ [x_bin z_bin]
    # , [x_bin z_bin]
    # ... one for each triangle
    # ]
    triangle_bins = np.floor_divide(triangle_centres, chunk_size)
    # Find all unique bins so we can iterate over them
    unique_bins = np.unique(triangle_bins, axis=0)
    result: Dict[Bin, TransformedRenderChunkData] = dict()
    for bin_arr in unique_bins:
        key = tuple(bin_arr)
        # Strategy here:
        # 1) Mask off the triangles according to the bin
        # 2) Squash that array (unmask)
        # 3) Substitute in vertices, and do np.unique to get new indices and vertices
        # mask = np.logical_not(np.all(np.equal(triangle_bins, key), axis=1))
        mask = np.all(np.equal(triangle_bins, key), axis=1)
        # TODO not flat
        these_flat_triangles = abc[mask]
        # these_flat_triangles = np.ma.masked_where(mask, triangle_verts).compressed()  # type: ignore
        # This squashes the vertices we need for this chunk and constructs the
        # reindexed triangle indices array (which is flat).
        (vertices, flat_indices) = np.unique(
            chunk.vertices[these_flat_triangles],
            return_inverse=True,
        )
        triangles = flat_indices.reshape((-1, 3))
        result[key] = TransformedRenderChunkData(
            type=chunk.type,
            vertices=vertices,
            triangles=triangles,
            bounding_box=compute_bounding_box_from_positions(vertices["position"]),
            texture_index_1=chunk.texture_index_1,
            texture_index_2=chunk.texture_index_2,
            specular_texture_index=chunk.specular_texture_index,
            shadow_texture_index=chunk.shadow_texture_index,
            chunk_distance=chunk.chunk_distance,
            uv_velocity=chunk.uv_velocity,
        )
    return result


def not_quite_unique(
    verts: NumpyArray, tris: NumpyArray
) -> Tuple[NumpyArray, NumpyArray]:
    """Optimisation over using np.unique at every level: sometimes we _know_ we
    will need to split again later (when there are lots of triangles), so we
    can avoid unique until later (when there are less triangles for unique to
    choke on while sorting).
    """
    if len(tris) > 3 * (2**16):
        vs = verts[tris].reshape(-1)
        return (vs, np.arange(len(vs)))
    else:
        return np.unique(
            verts[tris],
            return_inverse=True,
        )


def split_chunk_along_axis(
    axis_index: int,
    midpoint: float,
    triangle_centres: NumpyArray,
    chunk: TransformedRenderChunkData,
) -> Tuple[Optional[TransformedRenderChunkData], Optional[TransformedRenderChunkData]]:
    tri_axis_centres = triangle_centres[:, axis_index]
    (left_tris, right_tris) = split_array_by(
        chunk.triangles, tri_axis_centres < midpoint
    )

    def process_side(tris: NumpyArray) -> Optional[TransformedRenderChunkData]:
        # It's possible we are splitting this chunk outside of its bounds
        # (because the split point is determined by many chunks).
        if len(tris) == 0:
            return None

        (vertices, flat_indices) = not_quite_unique(chunk.vertices, tris)
        # Reshape indices into triangle triplets
        triangles = flat_indices.reshape((-1, 3))

        return TransformedRenderChunkData(
            type=chunk.type,
            vertices=vertices,
            triangles=triangles,
            bounding_box=compute_bounding_box_from_positions(vertices["position"]),
            texture_index_1=chunk.texture_index_1,
            texture_index_2=chunk.texture_index_2,
            specular_texture_index=chunk.specular_texture_index,
            shadow_texture_index=chunk.shadow_texture_index,
            chunk_distance=chunk.chunk_distance,
            uv_velocity=chunk.uv_velocity,
        )

    return (process_side(left_tris), process_side(right_tris))


def split_block_along_axis(
    axis_index: int,
    midpoint: float,
    main_triangle_centres: Optional[NumpyArray],
    far_triangle_centres: Optional[NumpyArray],
    block: ObjectBlock,
) -> Tuple[Optional[ObjectBlock], Optional[ObjectBlock]]:
    def process_side(
        main_tris: Optional[NumpyArray],
        far_tris: Optional[NumpyArray],
    ) -> Optional[ObjectBlock]:
        def empty(x: Optional[NumpyArray]) -> bool:
            return x is None or len(x) == 0

        # It's possible we are splitting this block outside of its bounds
        # (because the split point is determined by many chunks).
        if empty(main_tris) and empty(far_tris):
            return None

        if main_tris is None:
            main_tris = np.empty((0, 3), dtype=int)
        if far_tris is None:
            far_tris = np.empty((0, 3), dtype=int)
        all_tris = np.concatenate((main_tris, far_tris))

        (vertices, all_flat_indices) = not_quite_unique(block.vertices, all_tris)
        # Reshape indices into triangle triplets
        triangles = all_flat_indices.reshape((-1, 3))
        main_triangles = triangles[: len(main_tris)]
        far_triangles = triangles[len(main_tris) :]

        if len(main_triangles) > 0 and len(far_triangles) == 0:
            lod = block.lod
            main_buffer = main_triangles
            far_buffer = None
        elif len(main_triangles) == 0 and len(far_triangles) > 0:
            lod = ObjectBlockLOD.FAR_GEOMETRY_FROM_MAIN_BUFFER
            main_buffer = far_triangles
            far_buffer = None
        elif len(main_triangles) > 0 and len(far_triangles) > 0:
            lod = ObjectBlockLOD.FAR_GEOMETRY_FROM_FAR_BUFFER
            main_buffer = main_triangles
            far_buffer = far_triangles
        else:
            raise errors.RBRAddonBug(
                "There should be triangles at this stage, this is an addon bug"
            )

        return ObjectBlock(
            render_state_flags=block.render_state_flags,
            diffuse_texture_index_1=block.diffuse_texture_index_1,
            diffuse_texture_index_2=block.diffuse_texture_index_2,
            vertices=vertices,
            lod=lod,
            main_buffer=main_buffer,
            far_buffer=far_buffer,
            bounding_box=compute_bounding_box_from_positions(vertices["position"]),
        )

    main_left_tris = None
    main_right_tris = None
    if main_triangle_centres is not None:
        main_tri_axis_centres = main_triangle_centres[:, axis_index]
        (main_left_tris, main_right_tris) = split_array_by(
            block.main_buffer, main_tri_axis_centres < midpoint
        )
    far_left_tris = None
    far_right_tris = None
    if far_triangle_centres is not None:
        far_tri_axis_centres = far_triangle_centres[:, axis_index]
        (far_left_tris, far_right_tris) = split_array_by(
            block.far_buffer, far_tri_axis_centres < midpoint
        )

    return (
        process_side(main_left_tris, far_left_tris),
        process_side(main_right_tris, far_right_tris),
    )


def recursive_split(
    logger: Logger,
    chunks: List[TransformedRenderChunkData],
    object_blocks: List[ObjectBlock],
    chunk_size: float,
    path: str = "R",
) -> List[Tuple[List[TransformedRenderChunkData], List[ObjectBlock]]]:
    """Recursively split the given chunks by the longest axis.
    Returns a nested list, the outer list should become a GeomBlock.
    """
    all_triangle_centres = []
    vert_counts: Dict[NumpyDType, int] = dict()

    def go_with_verts_and_triangles(
        vertices: NumpyArray,
        triangles: NumpyArray,
    ) -> NumpyArray:
        # We may have no triangles left from a previous split
        if len(triangles) == 0:
            return None

        if len(vertices) == 0:
            raise errors.RBRAddonBug("No vertices left in go_with_verts_and_triangles")

        # Keep track of vertex count (per dtype) to prevent triangle buffer
        # overflow
        if vertices.dtype in vert_counts:
            vert_counts[vertices.dtype] += len(vertices)
        else:
            vert_counts[vertices.dtype] = len(vertices)

        xyz = structured_to_unstructured(vertices["position"])
        abc = triangles
        # Create a 3D array:
        # [ [ [x y z] [x y z] [x y z] ]
        # , [ [x y z] [x y z] [x y z] ]
        # ... one for each triangle
        # ]
        triangle_verts = np.take(xyz, abc, axis=0)
        # Collapse it to a 2D array of average position (triangle centre)
        # [ [x y z]
        # , [x y z]
        # ... one for each triangle
        # ]
        triangle_centres = np.average(triangle_verts, axis=1)
        all_triangle_centres.append(triangle_centres)
        return triangle_centres

    chunks_and_tris = []
    for chunk in chunks:
        triangle_centres = go_with_verts_and_triangles(chunk.vertices, chunk.triangles)
        if triangle_centres is None:
            continue
        chunks_and_tris.append((chunk, triangle_centres))

    blocks_and_tris = []
    for block in object_blocks:
        main_triangle_centres = go_with_verts_and_triangles(
            block.vertices, block.main_buffer
        )
        far_triangle_centres = None
        if block.far_buffer is not None:
            far_triangle_centres = go_with_verts_and_triangles(
                block.vertices, block.far_buffer
            )
        blocks_and_tris.append((block, main_triangle_centres, far_triangle_centres))

    if len(all_triangle_centres) > 0:
        concat_centres = np.concatenate(all_triangle_centres)
    else:
        return []

    logger.info(
        f"Split level {len(path)} path {path} with {len(concat_centres)} triangles",
        end="\r",
    )

    # We previously unique'd the vertices so this should give an accurate
    # reading on whether we need to split the block further.
    VERT_LIMIT = 2**16
    exceeded_limit = any([c > VERT_LIMIT for c in vert_counts.values()])

    # Find the longest axis
    maxi = np.amax(concat_centres, axis=0)
    mini = np.amin(concat_centres, axis=0)
    span = maxi - mini
    longest_axis = np.amax(span)
    axis_arr = np.where(span == longest_axis)
    longest_axis_index = axis_arr[0][0]

    # If the only geometry is "ANY" then we're probably far from the road and
    # quite low poly. So to avoid creating many chunks with a handful of
    # triangles, we increase the chunk size.
    oversized = longest_axis > chunk_size
    if all([c.chunk_distance is RenderChunkDistance.ANY for c in chunks]):
        oversized = longest_axis > chunk_size * 10

    if oversized or exceeded_limit:
        midpoint = np.average(concat_centres, axis=0)[longest_axis_index]
        # Split the geom block chunks along the longest axis
        left_chunks = []
        right_chunks = []
        for chunk, tris in chunks_and_tris:
            (left_chunk, right_chunk) = split_chunk_along_axis(
                axis_index=longest_axis_index,
                midpoint=midpoint,
                triangle_centres=tris,
                chunk=chunk,
            )
            if left_chunk is not None:
                left_chunks.append(left_chunk)
            if right_chunk is not None:
                right_chunks.append(right_chunk)
        # Split the object block chunks along the longest axis
        left_blocks = []
        right_blocks = []
        for block, main_tris, far_tris in blocks_and_tris:
            (left_block, right_block) = split_block_along_axis(
                axis_index=longest_axis_index,
                midpoint=midpoint,
                far_triangle_centres=far_tris,
                main_triangle_centres=main_tris,
                block=block,
            )
            if left_block is not None:
                left_blocks.append(left_block)
            if right_block is not None:
                right_blocks.append(right_block)
        # Recursively split each side again
        result = recursive_split(
            logger=logger,
            chunks=left_chunks,
            object_blocks=left_blocks,
            chunk_size=chunk_size,
            path=path + "L",
        )
        result.extend(
            recursive_split(
                logger=logger,
                chunks=right_chunks,
                object_blocks=right_blocks,
                chunk_size=chunk_size,
                path=path + "R",
            )
        )
        return result
    else:
        return [(chunks, object_blocks)]


def fixup_chunk_triangles_dtype(
    chunk: TransformedRenderChunkData,
) -> TransformedRenderChunkData:
    """Change unstructured triangles to the triangle_indices dtype for export"""
    chunk.triangles = unstructured_to_structured(
        np.flip(chunk.triangles, axis=1),
        dtype=dtypes.triangle_indices,
    )
    return chunk


def fixup_block_triangles_dtype(
    block: ObjectBlock,
) -> ObjectBlock:
    """Change unstructured triangles to the triangle_indices dtype for export"""
    block.main_buffer = unstructured_to_structured(
        np.flip(block.main_buffer, axis=1),
        dtype=dtypes.triangle_indices,
    )
    if block.far_buffer is not None:
        block.far_buffer = unstructured_to_structured(
            np.flip(block.far_buffer, axis=1),
            dtype=dtypes.triangle_indices,
        )
    return block


def split_super_chunks(
    logger: Logger,
    chunk_size: float,
    super_chunks: List[TransformedRenderChunkData],
    super_object_blocks: List[ObjectBlock],
) -> List[WorldChunk]:
    """Given a bunch of "super objects" (objects which do not conform to RBR's
    chunk boundaries or vertex count limits), split them up so they _do_
    conform.
    """
    nested_chunks = logger.section(
        "Splitting super chunks into world chunks",
        lambda: recursive_split(
            logger,
            super_chunks,
            super_object_blocks,
            chunk_size,
        ),
        make_end_msg=lambda chunks: f"Split into {len(chunks)} chunks",
    )

    def build_world_chunks() -> List[WorldChunk]:
        world_chunks = []
        for chunks, blocks in nested_chunks:
            gb_bounding_box = AaBbBoundingBox.unions([c.bounding_box for c in chunks])
            ob_bounding_box = AaBbBoundingBox.unions([b.bounding_box for b in blocks])
            if gb_bounding_box is None:
                if ob_bounding_box is None:
                    raise errors.RBRAddonBug(
                        "Missing both geom block and object block bounding boxes"
                    )
                wc_bounding_box = ob_bounding_box
            elif ob_bounding_box is None:
                if gb_bounding_box is None:
                    raise errors.RBRAddonBug(
                        "Missing both geom block and object block bounding boxes"
                    )
                wc_bounding_box = gb_bounding_box
            else:
                wc_bounding_box = AaBbBoundingBox.union(
                    gb_bounding_box, ob_bounding_box
                )
            block_segment = None
            if ob_bounding_box is not None:
                block_segment = ObjectBlockSegment(
                    blocks_1=[fixup_block_triangles_dtype(b) for b in blocks],
                    blocks_2=[],
                )
            world_chunks.append(
                WorldChunk(
                    bounding_box=wc_bounding_box,
                    geom_block=GeomBlock(
                        chunks=[fixup_chunk_triangles_dtype(c) for c in chunks],
                        bounding_box=(
                            gb_bounding_box
                            if gb_bounding_box is not None
                            else wc_bounding_box
                        ),
                    ),
                    object_block_segment=block_segment,
                    vec=VisibleObjectVec([Vector3(0, 0, 0)] * 5),  # TODO
                )
            )
        return world_chunks

    return logger.section(
        "Building world chunks",
        lambda: build_world_chunks(),
    )

    # This is the "chunk then split" method
    # bins: Dict[Bin, List[TransformedRenderChunkData]] = dict()
    # for super_chunk in super_chunks:
    #    for k, v in split_by_chunk_size(super_chunk, chunk_size).items():
    #        if k in bins:
    #            bins[k].append(v)
    #        else:
    #            bins[k] = [v]
    # world_chunks = []
    # for k, outer_chunks in bins.items():
    #    nested_chunks = recursive_split(outer_chunks, chunk_size)
    #    for chunks in nested_chunks:
    #        world_chunks.append(WorldChunk(
    #            bounding_box=chunks[0].bounding_box,  # TODO
    #            geom_block=GeomBlock(
    #                chunks=fixup_triangles_dtype(chunks),
    #                bounding_box=chunks[0].bounding_box,  # TODO
    #            ),
    #            object_block_segment=None, # TODO
    #            vec=VisibleObjectVec([Vector3(0, 0, 0)] * 5), # TODO
    #        ))
    # return world_chunks
