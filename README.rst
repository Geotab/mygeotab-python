MyGeotab
========

.. image:: https://travis-ci.org/Geotab/mygeotab-python.svg?branch=master
    :target: https://travis-ci.org/Geotab/mygeotab-python
    
.. image:: https://readthedocs.org/projects/mygeotab-python/badge/?version=latest
    :target: https://readthedocs.org/projects/mygeotab-python/?badge=latest
    :alt: Documentation Status


An Apache2 Licensed, unofficial Python client for the MyGeotab API.

Also bundled is the "myg" command line tool, which is a sandboxed console for quickly querying and operating on
MyGeotab data.


Features
--------

- Automatic serializing and de-serializing of JSON results
- Clean, Pythonic API for querying data
- Cross-platform and compatible with Python 2.7.6 and Python 3.4


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
