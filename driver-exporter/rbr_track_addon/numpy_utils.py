import numpy as np

from rbr_track_formats.common import NumpyArray


def srgb_to_linear(a: NumpyArray) -> NumpyArray:
    return np.where(
        a <= 0.04045,
        a / 12.92,
        ((a + 0.055) / 1.055) ** 2.4,
    )


def linear_to_srgb(a: NumpyArray) -> NumpyArray:
    return np.where(
        a <= 0.0031308,
        a * 12.92,
        1.055 * a ** (1 / 2.4) - 0.055,
    )


def rgb_avg(color: NumpyArray) -> NumpyArray:
    # Dot product across one axis
    dot = color.sum(axis=1)
    return np.reshape(dot, (-1, 1))


def rgb_to_bw(color: NumpyArray) -> NumpyArray:
    # See blender source: IMB_colormanagement_get_luminance
    # From blender config files
    luma = np.array([[0.2126, 0.7152, 0.0722]])
    # Dot product across one axis
    dot = (color * luma).sum(axis=1)
    return np.reshape(dot, (-1, 1))


def rgb_to_hsv(rgb: NumpyArray) -> NumpyArray:
    """Convert RGB values in a (-1, 3) shape numpy array to HSV values.
    This is a vectorised implementation of source / blender / blenlib / intern
    / math_color.c / rgb_to_hsv.
    """
    (r, g, b) = np.hsplit(rgb, 3)

    # SWAP(g, b)
    g1 = np.where(g < b, b, g)
    b1 = np.where(g < b, g, b)
    k1 = np.where(g < b, -1, 0)

    # SWAP(r, g)
    r2 = np.where(r < g1, g1, r)
    g2 = np.where(r < g1, r, g1)
    k2 = np.where(r < g1, -2 / 6 - k1, k1)
    min_gb: NumpyArray = np.where(r < g1, np.minimum(g2, b1), b1)

    chroma = r2 - min_gb

    h = np.abs(k2 + (g2 - b1) / (6 * chroma + 1e-20))
    s = chroma / (r2 + 1e-20)
    v = r2
    return np.hstack((h, s, v))


def clamp(arr: NumpyArray, low: NumpyArray, high: NumpyArray) -> NumpyArray:
    return np.maximum(np.minimum(arr, high), low)


def saturate(a: NumpyArray) -> NumpyArray:
    return clamp(a, 0, 1)


def fract(a: NumpyArray) -> NumpyArray:
    return a - np.floor(a)


def safe_divide(a: NumpyArray, b: NumpyArray) -> NumpyArray:
    return np.where(b != 0, a / b, 0)


def smoothstep(edge0: NumpyArray, edge1: NumpyArray, x: NumpyArray) -> NumpyArray:
    t = safe_divide(x - edge0, edge1 - edge0)
    return np.where(
        x < edge0,
        0,
        np.where(
            x >= edge1,
            1,
            (3 - 2 * t) * (t * t),
        ),
    )


def smootherstep(edge0: NumpyArray, edge1: NumpyArray, x: NumpyArray) -> NumpyArray:
    x = clamp(safe_divide((x - edge0), (edge1 - edge0)), 0, 1)
    return x * x * x * (x * (x * 6 - 15) + 10)


def smoothminf(a: NumpyArray, b: NumpyArray, c: NumpyArray) -> NumpyArray:
    h = safe_divide(np.fmax(c - np.fabs(a - b), 0), c)
    return np.where(
        c != 0,
        np.fmin(a, b) - h * h * h * c * (1 / 6),
        np.fmin(a, b),
    )


def hsv_to_rgb(hsv: NumpyArray) -> NumpyArray:
    """Convert HSV values in a (-1, 3) shape numpy array to RGB values.
    This is a vectorised implementation of source / blender / blenlib / intern
    / math_color.c / hsv_to_rgb.
    """
    (h, s, v) = np.hsplit(hsv, 3)

    nr = clamp(np.abs(h * 6 - 3) - 1, 0, 1)
    ng = clamp(2 - np.abs(h * 6 - 2), 0, 1)
    nb = clamp(2 - np.abs(h * 6 - 4), 0, 1)

    nrgb = np.hstack((nr, ng, nb))
    return ((nrgb - 1) * s + 1) * v
