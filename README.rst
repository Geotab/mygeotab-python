MyGeotab
========

.. image:: https://github.com/Geotab/mygeotab-python/workflows/Python%20package/badge.svg
    :target: https://github.com/Geotab/mygeotab-python
    :alt: Build Status

.. image:: https://readthedocs.org/projects/mygeotab-python/badge/?version=latest
    :target: https://mygeotab-python.readthedocs.io/en/latest/
    :alt: Documentation

.. image:: https://img.shields.io/codecov/c/github/Geotab/mygeotab-python/main.svg?style=flat
    :target: https://codecov.io/gh/Geotab/mygeotab-python
    :alt: Code Coverage

.. image:: https://img.shields.io/pypi/v/mygeotab.svg?style=flat
    :target: https://pypi.python.org/pypi/mygeotab
    :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/mygeotab.svg
    :target: https://pypi.python.org/pypi/mygeotab
    :alt: Python Versions

.. image:: https://img.shields.io/pypi/l/mygeotab.svg
    :target: https://pypi.python.org/pypi/mygeotab
    :alt: License


A Python client for the `MyGeotab SDK <https://geotab.github.io/sdk/>`_.

Features
--------

- Automatic serializing and deserializing of API call results
- Clean, Pythonic API for querying data
- Cross-platform and compatible with Python 3.7+
- A `myg` command-line tool for interactively working with data in a terminal

Usage
-----

It's very easy to get started once you've registered a `MyGeotab <https://www.geotab.com/fleet-management-software/>`__ database:

.. code-block:: python

    import mygeotab

    client = mygeotab.API(username='hello@example.com', password='mypass', database='MyDatabase')
    client.authenticate()

    devices = client.get('Device', name='%Test Dev%')

    print(devices)

    # [{'maxSecondsBetweenLogs': 200.0,
    #   'activeTo': '2050-01-01',
    #   'minAccidentSpeed': 3.0,
    #   'ignoreDownloadsUntil': '1986-01-01',
    #   'name': 'Test Device',
    #   'idleMinutes': 3.0,
    #   ......

You can also make calls asynchronously via `asyncio <https://docs.python.org/3/library/asyncio.html>`__:

.. code-block:: python

    import asyncio
    import mygeotab

    client = mygeotab.API(username='hello@example.com', password='mypass', database='MyDatabase')
    client.authenticate()

    async def get_device():
      return await client.get_async('Device', name='%Test Dev%')
    
    devices = loop.run_until_complete(get_device())
    print(devices)

    # [{'maxSecondsBetweenLogs': 200.0,
    #   'activeTo': '2050-01-01',
    #   'minAccidentSpeed': 3.0,
    #   'ignoreDownloadsUntil': '1986-01-01',
    #   'name': 'Test Device',
    #   'idleMinutes': 3.0,
    #   ......

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
