.. MyGeotab Python SDK documentation master file, created by
   sphinx-quickstart on Wed Oct  1 20:55:06 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to MyGeotab Python SDK's documentation!
===============================================

An Apache2 Licensed, unofficial Python client for the MyGeotab API.

Also bundled is the "mygeotab" command line tool, which is a sandboxed console for quickly querying and operating on
MyGeotab data.


Features
--------

- Automatic serializing and deserializing of JSON results
- Clean, Pythonic API for querying data
- Cross-platform and compatible with Python 2.7.6 and Python 3.4


Usage
-----

.. code-block:: python

    >>> import mygeotab
    >>> api = mygeotab.API(username='hello@example.com', password='mypass', database='DemoDB')
    >>> api.authenticate()
    >>> api.call('Get', 'Device', search=dict(name='%Test Dev%'))
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

    $ pip install git+https://github.com/aaront/mygeotab

Command Line Interface
----------------------

Installing this package also installs a command line tool `mygeotab` that provides a console for quickly
querying and interacting with data.

.. toctree::
   :maxdepth: 2

   commandline

API Reference
-------------

If you are looking for information on a specific function, class, or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api

