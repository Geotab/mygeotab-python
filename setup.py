# -*- coding: utf-8 -*-

import re
import ast

from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')
with open('mygeotab/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

try:
    with open('README.rst', 'r') as f:
        readme = f.read()
    with open('CHANGELOG.rst', 'r') as f:
        changelog = f.read()
except IOError:
    readme = ''
    changelog = ''

setup(
    name='mygeotab',
    author='Aaron Toth',
    version=version,
    url='https://github.com/geotab/mygeotab-python',
    description='An unofficial Python client for the MyGeotab API',
    long_description=readme + '\n\n' + changelog,
    extras_require={
        'console': ['ipython'],
        'async': ['aiohttp']
    },
    test_suite="tests",
    include_package_data=True,
    packages=find_packages(),
    package_data={'': ['LICENSE']},
    package_dir={'mygeotab': 'mygeotab'},
    license='Apache 2.0',
    entry_points='''
        [console_scripts]
        myg=mygeotab.cli:main
    ''',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries'
    ),
)
