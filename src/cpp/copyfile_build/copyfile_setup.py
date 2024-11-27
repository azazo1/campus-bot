"""
copyfile_build 模块编译脚本, 直接运行即可编译.
"""
from pathlib import Path

from Cython.Build import cythonize
from setuptools import setup, Extension

this_dir = Path(__file__).parent

modules = [
    Extension(
        name="copyfile",
        sources=[str(this_dir / "copyfile.pyx")],
        language="c++",
        libraries=['kernel32', 'user32']
    )
]


def build():
    return setup(
        ext_modules=cythonize(modules, language_level=3),
        script_args=[
            "build_ext",
            f"--build-lib={this_dir.parent}",
            f"--build-temp={this_dir / 'build'}"
        ],

    )


if __name__ == '__main__':
    print(build())
