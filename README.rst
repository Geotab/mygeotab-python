MyGeotab
========

.. image:: https://img.shields.io/circleci/project/github/Geotab/mygeotab-python/master.svg?style=flat
    :target: https://circleci.com/gh/Geotab/mygeotab-python
    :alt: Build Status

.. image:: https://img.shields.io/codecov/c/github/Geotab/mygeotab-python/master.svg?style=flat
    :target: https://codecov.io/gh/Geotab/mygeotab-python
    :alt: Code Coverage

.. image:: https://img.shields.io/pypi/v/mygeotab.svg?style=flat
    :target: https://pypi.python.org/pypi/mygeotab
    :alt: PyPI Version

.. image:: https://img.shields.io/pypi/dm/mygeotab.svg?style=flat
    :target: https://pypi.python.org/pypi/mygeotab
    :alt: PyPI Downloads

.. image:: https://readthedocs.org/projects/mygeotab-python/badge/?version=latest
    :target: https://readthedocs.org/projects/mygeotab-python/?badge=latest
    :alt: Documentation Status



An Apache2 Licensed, unofficial Python client for the `MyGeotab SDK <http://sdk.geotab.com>`_.

Also bundled is the "myg" command line tool, which is a sandboxed console for quickly querying and operating on
MyGeotab data.

Features
--------

- Automatic serializing and de-serializing of JSON results
- Clean, Pythonic API for querying data
- Cross-platform and compatible with Python 2.7.9+, 3.4+, and pypy 4+

Usage
-----

.. code-block:: python

    >>> import mygeotab
    >>> api = mygeotab.API(username='hello@example.com', password='mypass', database='DemoDB')
    >>> api.authenticate()
    >>> api.get('Device', search=dict(name='%Test Dev%'))
    [{'maxSecondsBetweenLogs': 200.0,
      'activeTo': '2050-01-01',
      'minAccidentSpeed': 3.0,
      'ignoreDownloadsUntil': '1986-01-01',
      'name': 'Test Device',
      'idleMinutes': 3.0,
      ......

Installation
------------

To install the MyGeotab library and command line tool:

.. code-block:: bash

    $ pip install mygeotab

or for the bleeding-edge version:

.. code-block:: bash

    $ pip install git+https://github.com/geotab/mygeotab-python

Documentation
-------------

Read the docs at `<http://mygeotab-python.readthedocs.org>`_
