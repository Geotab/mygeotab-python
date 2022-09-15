# -*- coding: utf-8 -*-

import ast
import re
import sys

from setuptools import setup


_version_re = re.compile(r"__version__\s+=\s+(.*)")
with open("mygeotab/__init__.py", "rb") as f:
    version = str(ast.literal_eval(_version_re.search(f.read().decode("utf-8")).group(1)))

try:
    with open("README.rst", "r") as f:
        readme = f.read()
    with open("CHANGELOG.rst", "r") as f:
        changelog = f.read()
except IOError:
    readme = ""
    changelog = ""

py_version = sys.version_info[:3]

if py_version < (2, 7, 9):
    raise RuntimeError("This package requres Python 2.7.9+")

packages = ["mygeotab", "mygeotab.ext"]
if py_version >= (3, 6, 0):
    packages.append("mygeotab.async")  # Deprecated
    packages.append("mygeotab.py3")

setup(
    name="mygeotab",
    author="Aaron Toth",
    version=version,
    url="https://github.com/geotab/mygeotab-python",
    description="A Python client for the MyGeotab SDK",
    long_description=readme + "\n\n" + changelog,
    extras_require={"notebook": ["pandas"], ":python_version>='3.6'": ["aiohttp>=3.8.1,<4", "python-rapidjson"]},
    test_suite="tests",
    include_package_data=True,
    packages=packages,
    package_data={"": ["LICENSE"]},
    license="Apache 2.0",
    install_requires=["requests", "click", "pytz", "arrow", "six"],
    setup_requires=["wheel"],
    entry_points="""
        [console_scripts]
        myg=mygeotab.cli:main
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
    ],
)
