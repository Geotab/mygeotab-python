API
===

The full API reference for all public classes and functions.

Querying Data
-------------

The top-level :class:`mygeotab.API` class is the async subclass and exposes both
synchronous methods (``call``, ``get``, ``add``, ``set``, ``remove``,
``multi_call``) and their async equivalents (``call_async``, ``get_async``, etc.).

.. module:: mygeotab.api_async

.. autoclass:: API
   :inherited-members:
   :members:

.. autoclass:: mygeotab.api.MyGeotabException

.. autoclass:: mygeotab.api.TimeoutException

Credentials & Authentication
-----------------------------

.. autoclass:: mygeotab.api.Credentials
   :members:

.. autoclass:: mygeotab.api.AuthenticationException

Unauthenticated Server Calls
-----------------------------

.. autofunction:: mygeotab.api.server_call

.. autofunction:: mygeotab.api_async.server_call_async

Date Helpers
------------

.. automodule:: mygeotab.dates
   :members:

Extras
------

EntityList
~~~~~~~~~~

.. autoclass:: mygeotab.ext.entitylist.API
   :inherited-members:
   :members:

.. autoclass:: mygeotab.ext.entitylist.EntityList
   :members:

Data Feed
~~~~~~~~~

.. autoclass:: mygeotab.ext.feed.DataFeed
   :members:

.. autoclass:: mygeotab.ext.feed.DataFeedListener
   :members:
