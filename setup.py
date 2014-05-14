# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

import mygeotab

setup(
    name='mygeotab',
    author='Aaron Toth',
    version=mygeotab.__version__,
    url='https://my.geotab.com/sdk',
    long_description=open('README.rst').read(),
    install_requires=[
        'requests',
        'click'
    ],
    extras_require = {
        'ipython_cli': ['ipython']
    },
    test_suite="tests",
    include_package_data=True,
    packages=find_packages(),
    entry_points='''
        [console_scripts]
        mygeotab=mygeotab.cli:main
    ''',
)