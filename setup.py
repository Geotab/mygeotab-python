# -*- coding: utf-8 -*-

import ast
import re
import sys

from setuptools import setup


_version_re = re.compile(r"__version__\s+=\s+(.*)")
with open("mygeotab/__init__.py", "rb") as f:
    version_match = _version_re.search(f.read().decode("utf-8"))
    assert version_match is not None
    version = str(ast.literal_eval(version_match.group(1)))

try:
    with open("README.rst", "r") as readme_f:
        readme = readme_f.read()
    with open("CHANGELOG.rst", "r") as changelog_f:
        changelog = changelog_f.read()
except IOError:
    readme = ""
    changelog = ""

py_version = sys.version_info[:3]

if py_version < (3, 10, 0):
    raise RuntimeError("This package requires Python 3.10.0+")

packages = ["mygeotab", "mygeotab.ext", "mygeotab.altitude"]

setup(
    name="mygeotab",
    author="Geotab Inc.",
    version=version,
    python_requires=">=3.10",
    url="https://github.com/geotab/mygeotab-python",
    description="A Python client for the MyGeotab SDK",
    long_description=f"{readme} \n\n {changelog}",
    long_description_content_type="text/x-rst",
    extras_require={"notebook": ["pandas"]},
    test_suite="tests",
    include_package_data=True,
    packages=packages,
    package_data={"": ["LICENSE"]},
    license="Apache 2.0",
    install_requires=[
        "requests",
        "urllib3",
        "click",
        "pytz",
        "arrow",
        "aiohttp[speedups]>=3.13.5,<4",
        "python-rapidjson",
    ],
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries",
    ],
)
