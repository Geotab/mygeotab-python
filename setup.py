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
        'requests'
    ],
    test_suite="tests",
    packages=find_packages(),
)