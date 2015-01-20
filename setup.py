# -*- coding: utf-8 -*-

import mygeotab

from setuptools import setup, find_packages

setup(
    name='mygeotab',
    author='Aaron Toth',
    version=mygeotab.__version__,
    url='https://github.com/aaront/mygeotab',
    description='An unofficial Python client for the MyGeotab API',
    long_description=open('README.rst').read(),
    install_requires=[
        'requests',
        'click'
    ],
    extras_require={
        'ipy': ['ipython']
    },
    test_suite="tests",
    include_package_data=True,
    packages=find_packages(),
    package_data={'': ['LICENSE']},
    package_dir={'mygeotab': 'mygeotab'},
    license='Apache 2.0',
    entry_points='''
        [console_scripts]
        mygeotab=mygeotab.cli:main
    ''',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries'
    ),
)