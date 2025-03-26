from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Set, Tuple
import enum


class Language(enum.Enum):
    EN = enum.auto()

    def pretty(self) -> str:
        if self is Language.EN:
            return "English"


class RBRAddonBug(Exception):
    """Errors which indicate a bug in the addon"""

    message: str


class RBRAddonError(Exception):
    """Errors which indicate a problem the user should fix"""

    def report(self, lang: Language) -> str:
        err_code = type(self).__name__
        return f"{err_code}: {self.format(lang)}"

    @abstractmethod
    def format(self, lang: Language) -> str:
        pass


@dataclass
class E0001(RBRAddonError):
    num_points: int
    max_points: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many points in the brake wall! Got {self.num_points} vertices but the maximum is {self.max_points}."


@dataclass
class E0002(RBRAddonError):
    layer_type: str
    missing_layer_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Brake wall {self.layer_type} vertex group '{self.missing_layer_name}' does not exist"


@dataclass
class E0003(RBRAddonError):
    position: List[float]

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            pos = [round(p) for p in self.position]
            return f"Brake wall vertex at {pos} has invalid vertex groups"


@dataclass
class E0004(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Brake wall mesh has no data to export"


@dataclass
class E0005(RBRAddonError):
    num_inner: int
    num_outer: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Brake wall mesh should have an equal number of inner and outer vertices. Found {self.num_inner} inner vertices and {self.num_outer} outer vertices."


@dataclass
class E0006(RBRAddonError):
    position: List[float]

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            pos = [round(p) for p in self.position]
            return f"Brake wall mesh is malformed! Vertex at {pos} has invalid edges."


@dataclass
class E0007(RBRAddonError):
    got_magic: str
    expected_magic: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Invalid magic in col file, got '{self.got_magic}' but expected '{self.expected_magic}'"


@dataclass
class E0008(RBRAddonError):
    value: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Bad value when unpacking collision tree data type: {self.value}"


@dataclass
class E0009(RBRAddonError):
    value: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Bad value when unpacking collision tree type: {self.value}"


@dataclass
class E0010(RBRAddonError):
    data_type: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unexpected collision tree data type: {self.data_type}"


@dataclass
class E0011(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Found vertex data in unexpected place for collision tree"


@dataclass
class E0012(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Padding bytes contain non-zero data in water surface"


@dataclass
class E0013(RBRAddonError):
    root_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unexpected root file node offset: got '{self.root_offset}' but expected '{self.expected_offset}'"


@dataclass
class E0014(RBRAddonError):
    tree_type: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                f"Unexpected collision tree type in col file root: '{self.tree_type}'"
            )


@dataclass
class E0015(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Non empty branch traversal in col file root"


@dataclass
class E0016(RBRAddonError):
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack the brake wall at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0017(RBRAddonError):
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack the wet surfaces at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0018(RBRAddonError):
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack the water surfaces at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0019(RBRAddonError):
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack the collision vertices at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0020(RBRAddonError):
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack the root collision tree at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0021(RBRAddonError):
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack the sub tree nodes at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0022(RBRAddonError):
    index: int
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack subtree '{self.index}' at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0023(RBRAddonError):
    index: int
    tree_type: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Subtree '{self.index}' has unsupported type: '{self.tree_type}'"


@dataclass
class E0024(RBRAddonError):
    index: int
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack subtree '{self.index}' vertices at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0025(RBRAddonError):
    index: int
    type: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack subtree '{self.index}' but encountered wrong type: '{self.type}'"


@dataclass
class E0026(RBRAddonError):
    index: int
    expected_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Trying to unpack subtree '{self.index}' collision tree at offset '{self.actual_offset}', but expected '{self.expected_offset}'"


@dataclass
class E0027(RBRAddonError):
    remaining: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Failed to unpack '{self.remaining}' bytes from the col file"


@dataclass
class E0028(RBRAddonError):
    fmt: str
    context: str
    overflow_offset: int
    actual_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unpacking format '{self.fmt}' overflowed ({self.actual_offset} > {self.overflow_offset}): {self.context}"


@dataclass
class E0029(RBRAddonError):
    context: str
    overflow_size: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unpacking bytes overflowed by {self.overflow_size} bytes: {self.context}"


@dataclass
class E0030(RBRAddonError):
    context: str
    position: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unpacking bytes at position {self.position} overflowed: {self.context}"


@dataclass
class E0031(RBRAddonError):
    contents: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Padding bytes are non-zero: '{self.contents}'"


@dataclass
class E0032(RBRAddonError):
    length: int
    divisor: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Invalid array length in binary format: length {self.length} does not get evenly divided by divisor {self.divisor}"


@dataclass
class E0033(RBRAddonError):
    loc: str
    count: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                f"Encountered suspiciously high count ({self.count}) for '{self.loc}'"
            )


@dataclass
class E0034(RBRAddonError):
    words: List[str]

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Couldn't parse Vector3 from ini string '{self.words}'"


@dataclass
class E0035(RBRAddonError):
    expected_magic: str
    actual_magic: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"DDS: Incorrect magic string, got '{self.actual_magic}' but expected '{self.expected_magic}'"


@dataclass
class E0036(RBRAddonError):
    flag: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"DDS: Missing flag {self.flag}"


@dataclass
class E0037(RBRAddonError):
    actual_size: int
    expected_size: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"DDS: Unexpected pixelformat size {self.actual_size}, expected {self.expected_size}"


@dataclass
class E0038(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "DDS texture is uncompressed, re-export with DXT1/3/5 compression"


@dataclass
class E0039(RBRAddonError):
    ascii_codec: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Invalid DXT codec: '{self.ascii_codec}'"


@dataclass
class E0040(RBRAddonError):
    inner_error: RBRAddonError
    file_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Failed to decode DDS file '{self.file_name}': {self.inner_error.report(lang)}"


@dataclass
class E0041(RBRAddonError):
    kind: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unsupported trigger kind found in sig trigger data: {self.kind}"


@dataclass
class E0042(RBRAddonError):
    kind: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unsupported trigger kind found in bool channel data: {self.kind}"


@dataclass
class E0043(RBRAddonError):
    count: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Found {self.count} bool channels but expected none"


@dataclass
class E0044(RBRAddonError):
    kind: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unsupported trigger kind found in real channel data: {self.kind}"


@dataclass
class E0045(RBRAddonError):
    value: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Real channel data contains non-zero time based flag {self.value}"


@dataclass
class E0046(RBRAddonError):
    expected_size: int
    actual_size: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Animation set descriptor has unexpected size {self.actual_size}, expected {self.expected_size}"


@dataclass
class E0047(RBRAddonError):
    bits: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Spline interpolation value has leftover bits {self.bits}"


@dataclass
class E0048(RBRAddonError):
    id: int
    unused_id: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Expected unused ID ({self.unused_id}) in trigger data to match actual ID ({self.id})"


@dataclass
class E0049(RBRAddonError):
    expected_header: str
    actual_header: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Incorrect header in DLS file, got '{self.actual_header}' but expected '{self.expected_header}'"


@dataclass
class E0050(RBRAddonError):
    section: str
    extra_bytes: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"DLS parser missed {self.extra_bytes} bytes when parsing {self.section}"


@dataclass
class E0051(RBRAddonError):
    section: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"DLS file is missing section {self.section}"


@dataclass
class E0052(RBRAddonError):
    value: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Unexpected fence type: {self.value}"


@dataclass
class E0053(RBRAddonError):
    actual_version: int
    expected_version: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Wrong FNC file version: expected {self.expected_version} but got {self.actual_version}"


@dataclass
class E0054(RBRAddonError):
    expected_length: int
    actual_length: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"FNC file has wrong number of texture names, got {self.actual_length} but expected {self.expected_length}"


@dataclass
class E0055(RBRAddonError):
    actual_x: int
    actual_y: int
    expected_x: int
    expected_y: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material in MAT file has bad dimensions: got ({self.actual_x}, {self.actual_y}) but expected ({self.expected_x}, {self.expected_y})"


@dataclass
class E0056(RBRAddonError):
    remaining_bytes: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Shadow file parser missed {self.remaining_bytes} bytes"


@dataclass
class E0057(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Missing render state in geom block object data"


@dataclass
class E0058(RBRAddonError):
    actual_size: int
    expected_size: int
    flags: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object data vertex size {self.actual_size} does not match expected size {self.expected_size} for flags '{self.flags}'"


@dataclass
class E0059(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Object data has specular texture but no diffuse textures"


@dataclass
class E0060(RBRAddonError):
    remainder: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS geom blocks: first triangle index is not divisible by 3, remainder={self.remainder}"


@dataclass
class E0061(RBRAddonError):
    pixel_shader: str
    render_type: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data has bad pixel shader ID {self.pixel_shader} for render type {self.render_type}"


@dataclass
class E0062(RBRAddonError):
    value: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data has unexpected value in flag: {self.value}"


@dataclass
class E0063(RBRAddonError):
    is_shadow: int
    raw_shadow_texture_index: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data has bad shadow texture values {self.is_shadow} {self.raw_shadow_texture_index}"


@dataclass
class E0064(RBRAddonError):
    is_specular: int
    raw_specular_texture_index: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data has bad specular texture values {self.is_specular} {self.raw_specular_texture_index}"


@dataclass
class E0065(RBRAddonError):
    num_textures: int
    index_1: int
    index_2: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data has bad texture values {self.num_textures} {self.index_1} {self.index_2}"


@dataclass
class E0066(RBRAddonError):
    vertex_shader: str
    render_type: str
    anim: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data has bad vertex shader ID {self.vertex_shader} for render type {self.render_type} {self.anim}"


@dataclass
class E0067(RBRAddonError):
    field: str
    value: float

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "LBS render chunk data UV velocity has values when it should be null: field '{self.field}' has value {self.value}"


@dataclass
class E0068(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Missing render state in object block data"


@dataclass
class E0069(RBRAddonError):
    value: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                f"Expected object block 'init' value to be zero, but got {self.value}"
            )


@dataclass
class E0070(RBRAddonError):
    actual_size: int
    expected_size: int
    flags: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object block has bad vertex size value '{self.actual_size}', expected '{self.expected_size}' due to flags '{self.flags}'"


@dataclass
class E0071(RBRAddonError):
    header_size: int
    expected_size: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"LBS segment header size '{self.header_size}' does not match expected value '{self.expected_size}'"


@dataclass
class E0072(RBRAddonError):
    expected_category: str
    actual_category: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Expected LBS segment category to be '{self.expected_category}' but got '{self.actual_category}'"


@dataclass
class E0073(RBRAddonError):
    missing_category: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"LBS file does not have required section '{self.missing_category}'"


@dataclass
class E0074(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Driveline point has non-zero unused data"


@dataclass
class E0075(RBRAddonError):
    use_local_rotation: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Shape collision mesh has unexpected value of 'use local rotation': {self.use_local_rotation}"


@dataclass
class E0076(RBRAddonError):
    expected_size: int
    actual_size: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"TRK segment header size '{self.actual_size}' does not match expected value '{self.expected_size}'"


@dataclass
class E0077(RBRAddonError):
    expected_category: str
    actual_category: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Expected TRK segment category to be '{self.expected_category}' but got '{self.actual_category}'"


@dataclass
class E0078(RBRAddonError):
    missing_category: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"TRK file does not have required section '{self.missing_category}'"


@dataclass
class E0079(RBRAddonError):
    offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Collision mesh tree node header has unexpected vertices offset '{self.offset}'"


@dataclass
class E0080(RBRAddonError):
    num_triangles: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Collision mesh tree root node has '{self.num_triangles}' triangles"


@dataclass
class E0081(RBRAddonError):
    actual_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Collision mesh tree root tree at unexpected offset '{self.actual_offset}', expected '{self.expected_offset}'"


@dataclass
class E0082(RBRAddonError):
    actual_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Collision mesh tree subtree at unexpected offset '{self.actual_offset}', expected '{self.expected_offset}'"


@dataclass
class E0083(RBRAddonError):
    num_geom_blocks: int
    num_object_blocks: int
    num_visible_objects: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Couldn't unpack world chunks with unequal numbers of blocks: {self.num_geom_blocks} geom blocks, {self.num_object_blocks} object blocks, {self.num_visible_objects} visible objects"


@dataclass
class E0084(RBRAddonError):
    num_geom_blocks: int
    num_visible_object_vecs: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Couldn't unpack world chunks with unequal numbers of blocks: {self.num_geom_blocks} geom blocks, {self.num_visible_object_vecs} visible object vecs"


@dataclass
class E0085(RBRAddonError):
    num_vertices: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Expected an even number of vertices in the brake wall, but got {self.num_vertices}"


@dataclass
class E0086(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Expected even brake wall index offset"


@dataclass
class E0087(RBRAddonError):
    actual_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Brake wall branch at unexpected offset '{self.actual_offset}', expected '{self.expected_offset}'"


@dataclass
class E0088(RBRAddonError):
    actual_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Brake wall header ended at unexpected offset '{self.actual_offset}', expected '{self.expected_offset}'"


@dataclass
class E0089(RBRAddonError):
    actual_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Brake wall tree at unexpected offset '{self.actual_offset}', expected '{self.expected_offset}'"


@dataclass
class E0090(RBRAddonError):
    actual_offset: int
    expected_offset: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Brake wall ended at unexpected offset '{self.actual_offset}', expected '{self.expected_offset}'"


@dataclass
class E0091(RBRAddonError):
    actual_length: int
    expected_length: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Visible object vecs have unexpected length '{self.actual_length}', expected '{self.expected_length}'"


@dataclass
class E0092(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                "Missing first diffuse texture for object with second diffuse texture"
            )


@dataclass
class E0093(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Missing diffuse texture for object with specular texture"


@dataclass
class E0094(RBRAddonError):
    name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Shape colmesh '{self.name}' has invalid type"


@dataclass
class E0095(RBRAddonError):
    name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Shape colmesh '{self.name}' has invalid type"


@dataclass
class E0096(RBRAddonError):
    name: str
    num_vertices: int
    max_vertices: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many vertices ({self.num_vertices}) for collision mesh '{self.name}', maximum {self.max_vertices}"


@dataclass
class E0097(RBRAddonError):
    name: str
    num_edges: int
    max_edges: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many edges ({self.num_edges}) for collision mesh '{self.name}', maximum {self.max_edges}"


@dataclass
class E0098(RBRAddonError):
    name: str
    num_faces: int
    max_faces: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many faces ({self.num_faces}) for collision mesh '{self.name}', maximum {self.max_faces}"


@dataclass
class E0099(RBRAddonError):
    num_meshes: int
    max_meshes: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many shape collision meshes: got {self.num_meshes} but the maximum is {self.max_meshes}"


@dataclass
class E0100(RBRAddonError):
    string: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Invalid surface type '{self.string}'"


@dataclass
class E0101(RBRAddonError):
    string: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Invalid surface age '{self.string}'"


@dataclass
class E0102(RBRAddonError):
    name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Couldn't parse track name from track settings: '{self.name}'"


@dataclass
class E0103(RBRAddonError):
    name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                f"Couldn't parse track specification from track settings: '{self.name}'"
            )


@dataclass
class E0104(RBRAddonError):
    object_name: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object '{self.object_name}' uses non-RBR material '{self.material_name}'"


@dataclass
class E0105(RBRAddonError):
    export_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Missing export directory named '{self.export_name}'"


@dataclass
class E0106(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Missing 'car location' object"


@dataclass
class E0107(RBRAddonError):
    texture_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material maps for texture '{self.texture_name}' don't cover all UV triangles"


@dataclass
class E0108(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' does not have a diffuse texture, but needs one for collision mesh export"


@dataclass
class E0109(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Missing world collision mesh"


@dataclass
class E0110(RBRAddonError):
    mesh_name: str
    attr_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Mesh '{self.mesh_name}' does not have required attribute '{self.attr_name}'"


@dataclass
class E0111(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Clamp shader node must be 'min/max'"


@dataclass
class E0112(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Color ramp shader node must be 'RGB'"


@dataclass
class E0113(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                "Color ramp shader node must use 'Constant' or 'Linear' interpolation"
            )


@dataclass
class E0114(RBRAddonError):
    node_tree: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Loop detected in shader tree '{self.node_tree}'"


@dataclass
class E0115(RBRAddonError):
    socket_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Geometry node '{self.socket_name}' is not yet supported"


@dataclass
class E0116(RBRAddonError):
    node_type: str
    socket_type: str
    baking_socket: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Can't bake for node '{self.node_type}' socket '{self.socket_type}' connected to '{self.baking_socket}'"


@dataclass
class E0117(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Could not find RBR shader"


@dataclass
class E0118(RBRAddonError):
    inner_error: RBRAddonError
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Failed to bake for material '{self.material_name}': {self.inner_error.report(lang)}"


@dataclass
class E0119(RBRAddonError):
    mesh_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"No materials in mesh '{self.mesh_name}'"


@dataclass
class E0120(RBRAddonError):
    texture_type: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Missing UV Map for {self.texture_type} in material '{self.material_name}'"


@dataclass
class E0121(RBRAddonError):
    image_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Image '{self.image_name}' is packed into the blend file. Images must be unpacked for exporting."


@dataclass
class E0122(RBRAddonError):
    image_name: str
    texture_name: str
    ideal_width: int
    ideal_height: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Image '{self.image_name}' for texture '{self.texture_name}' has incorrect size. Suggested size: {self.ideal_width}x{self.ideal_height}"


@dataclass
class E0123(RBRAddonError):
    texture_variant: str
    texture_name: str
    image_name: str
    expected_path: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Missing file for {self.texture_variant} RBR texture '{self.texture_name}'. Image '{self.image_name}' expected at path '{self.expected_path}'"


@dataclass
class E0124(RBRAddonError):
    texture_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                f"DDS files have different settings for texture '{self.texture_name}'"
            )


@dataclass
class E0125(RBRAddonError):
    texture_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"No image files found for texture '{self.texture_name}'"


@dataclass
class E0126(RBRAddonError):
    texture_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"No image files found for specular texture '{self.texture_name}'"


@dataclass
class E0127(RBRAddonError):
    object_name: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object '{self.object_name}' material '{self.material_name}' must have a texture, but has none"


@dataclass
class E0128(RBRAddonError):
    object_name: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object block '{self.object_name}' material '{self.material_name}' must use an alpha blend mode."


@dataclass
class E0129(RBRAddonError):
    object_name: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object blocks must have a single diffuse texture, but '{self.object_name}' material '{self.material_name}' has none"


@dataclass
class E0130(RBRAddonError):
    interactive_objects: Set[str]

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"{len(self.interactive_objects)} interactive objects are missing collision meshes. Objects: {', '.join(self.interactive_objects)}"


@dataclass
class E0131(RBRAddonError):
    num_zfar_objects: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Found {self.num_zfar_objects} render distance objects but expected one"


@dataclass
class E0132(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Render distance object must have the driveline as a parent"


@dataclass
class E0133(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Render distance object must be an object type of 'empty circle'"


@dataclass
class E0134(RBRAddonError):
    num_objects: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Expected one driveline object, found {self.num_objects}"


@dataclass
class E0135(RBRAddonError):
    driveline_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Driveline object '{self.driveline_name}' is not a spline"


@dataclass
class E0136(RBRAddonError):
    num_points: int
    max_points: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Driveline has too many points: maximum '{self.max_points}', got '{self.num_points}'"


@dataclass
class E0137(RBRAddonError):
    position: Tuple[float, float, float]

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Driveline not well formed at point {[round(x) for x in self.position]}"


@dataclass
class E0138(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' is not using nodes"


@dataclass
class E0139(RBRAddonError):
    material_name: str
    input_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' has unconnected texture socket '{self.input_name}'"


@dataclass
class E0140(RBRAddonError):
    material_name: str
    input_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' texture socket '{self.input_name}' is not connected to an RBR texture"


@dataclass
class E0141(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return (
                f"Material '{self.material_name}' contains an unconnected UV map socket"
            )


@dataclass
class E0142(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' contains an unsupported UV map connection"


@dataclass
class E0143(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' UV Velocity input must be disconnected"


@dataclass
class E0144(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' missing UV map input to UV velocity node"


@dataclass
class E0145(RBRAddonError):
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Material '{self.material_name}' has invalid UV map input to UV velocity node"


@dataclass
class E0146(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Mismatched number of material maps"


@dataclass
class E0147(RBRAddonError):
    mesh_name: str
    uv_map_layer: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Mesh '{self.mesh_name}' missing UV map layer '{self.uv_map_layer}' (required by material '{self.material_name}')"


@dataclass
class E0148(RBRAddonError):
    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return "Need a driveline object for exporting cameras or render distance"


@dataclass
class E0149(RBRAddonError):
    operation: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Vector math node operation '{self.operation}' not yet supported"


@dataclass
class E0150(RBRAddonError):
    object_name: str
    material_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Object '{self.object_name}' material '{self.material_name}' is not linked to data"


@dataclass
class E0151(RBRAddonError):
    material_name: str
    attr_type: str
    attr_domain: str
    mesh_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Mesh '{self.mesh_name}' material '{self.material_name}' is using an unsupported UV attribute type '{self.attr_type}' and domain '{self.attr_domain}'"


@dataclass
class E0152(RBRAddonError):
    object_name: str
    scale: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Interactive object '{self.object_name}' has scale '{self.scale}' but scale must be applied"


@dataclass
class E0153(RBRAddonError):
    object_name: str
    scale: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Shape collision mesh '{self.object_name}' has scale '{self.scale}' but scale must be applied"


@dataclass
class E0154(RBRAddonError):
    object_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Interactive object '{self.object_name}' has more than one collision mesh"


@dataclass
class E0155(RBRAddonError):
    object_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Interactive object '{self.object_name}' has no collision mesh"


@dataclass
class E0156(RBRAddonError):
    object_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Collision mesh '{self.object_name}' is not convex"


@dataclass
class E0157(RBRAddonError):
    object_name: str

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Wet surface '{self.object_name}' contains non-quad faces."


@dataclass
class E0158(RBRAddonError):
    num_maps: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many material maps ({self.num_maps})"


@dataclass
class E0159(RBRAddonError):
    num_wet_surfaces: int
    num_water_surfaces: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many wet ({self.num_wet_surfaces}) and water ({self.num_water_surfaces}) surfaces"


@dataclass
class E0160(RBRAddonError):
    num_checkpoints: int

    def format(self, lang: Language) -> str:
        if lang is Language.EN:
            return f"Too many split events on the driveline ({self.num_checkpoints}). There should be 2."
