import numpy
from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import numpy as np

common_include_dirs = [numpy.get_include(), "."]

extensions = [
    Extension(
        name="engine.math.affine",
        sources=["engine/math/affine.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.math.datatypes.vector2",
        sources=["engine/math/datatypes/vector2.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.math.datatypes.rect2",
        sources=["engine/math/datatypes/rect2.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.math.datatypes.transform2d",
        sources=["engine/math/datatypes/transform2d.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.math.datatypes.color",
        sources=["engine/math/datatypes/color.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.math.algorithms.geometry",
        sources=["engine/math/algorithms/geometry.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.math.algorithms.homography",
        sources=["engine/math/algorithms/homography.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.tools.colors",
        sources=["engine/graphics/tools/colors.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.pipeline.clipper",
        sources=["engine/graphics/rasterizer/pipeline/clipper.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.primitives.circle",
        sources=["engine/graphics/rasterizer/primitives/circle.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.primitives.line",
        sources=["engine/graphics/rasterizer/primitives/line.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.primitives.polygon",
        sources=["engine/graphics/rasterizer/primitives/polygon.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.primitives.rect",
        sources=["engine/graphics/rasterizer/primitives/rect.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.primitives.triangle",
        sources=["engine/graphics/rasterizer/primitives/triangle.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.primitives.point",
        sources=["engine/graphics/rasterizer/primitives/point.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
    Extension(
        name="engine.graphics.rasterizer.samplers.samplers",
        sources=["engine/graphics/rasterizer/samplers/samplers.pyx"],
        include_dirs=common_include_dirs,
        language="c",
    ),
]

setup(
    name="Engine",
    packages=find_packages(include=["engine", "engine.*", "game", "game.*"]),
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "initializedcheck": False,
            "embedsignature": True,
        },
        annotate=False,
    ),
    include_dirs=common_include_dirs,
)
