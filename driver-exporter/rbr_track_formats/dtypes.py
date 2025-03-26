import numpy as np

uv = np.dtype(
    [
        ("u", "<f"),
        ("v", "<f"),
    ]
)

vector3 = np.dtype(
    [
        ("x", "<f"),
        ("y", "<f"),
        ("z", "<f"),
    ]
)

# The left hand version of above.
vector3_lh = np.dtype(
    [
        ("x", "<f"),
        ("z", "<f"),
        ("y", "<f"),
    ]
)

color = np.dtype(
    [
        ("b", "<B"),
        ("g", "<B"),
        ("r", "<B"),
        ("a", "<B"),
    ]
)

triangle_indices_int = np.dtype(
    [
        ("a", "<I"),
        ("b", "<I"),
        ("c", "<I"),
    ]
)

triangle_indices = np.dtype(
    [
        ("a", "<H"),
        ("b", "<H"),
        ("c", "<H"),
    ]
)

position_color = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
    ]
)

single_texture = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
    ]
)

single_texture_specular = np.dtype(
    [
        ("position", vector3_lh),
        ("normal", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("specular_uv", uv),
        ("specular_strength", "<f"),
    ]
)

single_texture_shadow = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("shadow_uv", uv),
        ("shadow_strength", "<f"),  # TODO check this
    ]
)

single_texture_specular_shadow = np.dtype(
    [
        ("position", vector3_lh),
        ("normal", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("specular_uv", uv),
        ("specular_strength", "<f"),
        ("shadow_uv", uv),
        ("shadow_strength", "<f"),  # TODO check this
    ]
)

double_texture = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("diffuse_2_uv", uv),
    ]
)

double_texture_specular = np.dtype(
    [
        ("position", vector3_lh),
        ("normal", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("diffuse_2_uv", uv),
        ("specular_uv", uv),
        ("specular_strength", "<f"),
    ]
)

double_texture_shadow = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("diffuse_2_uv", uv),
        ("shadow_uv", uv),
        ("shadow_strength", "<f"),  # TODO check this
    ]
)

double_texture_specular_shadow = np.dtype(
    [
        ("position", vector3_lh),
        ("normal", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("diffuse_2_uv", uv),
        ("specular_uv", uv),
        ("specular_strength", "<f"),
        ("shadow_uv", uv),
        ("shadow_strength", "<f"),  # TODO check this
    ]
)


sway = np.dtype(
    [
        ("amplitude", "<f"),
        ("angular_frequency", "<f"),
        ("phase_offset", "<f"),
    ]
)

position_color_sway = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("sway", sway),
    ]
)

single_texture_sway = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("sway", sway),
    ]
)

double_texture_sway = np.dtype(
    [
        ("position", vector3_lh),
        ("color", color),
        ("diffuse_1_uv", uv),
        ("diffuse_2_uv", uv),
        ("sway", sway),
    ]
)
