MyGeotab
========

.. image:: https://github.com/Geotab/mygeotab-python/actions/workflows/pythonpackage.yml/badge.svg
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


A Python client for the `MyGeotab SDK <https://developers.geotab.com/>`_.

Features
--------

- Automatic serialization and deserialization of API call results
- Clean, Pythonic API for querying, adding, updating, and removing entities
- Both synchronous and ``async``/``await`` interfaces
- Cross-platform and compatible with Python 3.10+
- ``myg`` command-line tool for interactively exploring data in a terminal

Installation
------------

.. code-block:: bash

    $ pip install mygeotab

For the latest development version:

.. code-block:: bash

    $ pip install git+https://github.com/geotab/mygeotab-python

Usage
-----

Synchronous
~~~~~~~~~~~

.. code-block:: python

    import mygeotab

    client = mygeotab.API(
        username='hello@example.com',
        password='mypass',
        database='MyDatabase',
    )
    client.authenticate()

    devices = client.get('Device', name='%Test Dev%')
    print(devices)

    # [{'name': 'Test Device',
    #   'maxSecondsBetweenLogs': 200.0,
    #   'activeTo': '2050-01-01',
    #   ...}]

Asynchronous
~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    import mygeotab

    async def main():
        client = mygeotab.API(
            username='hello@example.com',
            password='mypass',
            database='MyDatabase',
        )
        client.authenticate()

        devices = await client.get_async('Device', name='%Test Dev%')
        print(devices)

    asyncio.run(main())

Command-line tool
~~~~~~~~~~~~~~~~~

The ``myg`` tool opens an interactive Python console pre-loaded with an
authenticated API object:

.. code-block:: bash

    $ myg console MyDatabase

    # Inside the console, `myg` is the active API object:
    >>> myg.get('Device', name='%Test%')

Manage saved sessions:

.. code-block:: bash

    $ myg sessions --list
    $ myg sessions remove MyDatabase

Documentation
-------------

Full API reference and guides are at `<https://mygeotab-python.readthedocs.io/en/latest/>`_.

License
-------

Apache 2.0. See `LICENSE <LICENSE>`_ for details.
