Extras
======

Optional extensions that add convenience on top of the core API.

EntityList
----------

:class:`mygeotab.ext.entitylist.EntityList` is a ``list`` subclass returned by the
extended :class:`mygeotab.ext.entitylist.API` wrapper. It adds helper methods that
make common result-handling patterns more concise.

.. code-block:: python

    from mygeotab.ext.entitylist import API

    api = API(username='hello@example.com', password='mypass', database='MyDatabase')
    api.authenticate()

    devices = api.get('Device')       # returns EntityList, not a plain list

    # Convenience properties
    first  = devices.first            # first item, or None if empty
    last   = devices.last             # last item, or None if empty
    device = devices[0:1].entity      # asserts exactly one result, returns it

    # Sort without mutating the original
    by_name = devices.sort_by('name')
    by_name_desc = devices.sort_by('name', reverse=True)

    # Export to a pandas DataFrame (requires: pip install mygeotab[notebook])
    df = devices.to_dataframe()
    df_normalized = devices.to_dataframe(normalize=True)  # flattens nested dicts

See the API reference for the full :class:`EntityList <mygeotab.ext.entitylist.EntityList>`
and :class:`entitylist.API <mygeotab.ext.entitylist.API>` documentation.

Data Feed
---------

:class:`mygeotab.ext.feed.DataFeed` polls ``GetFeed`` on a background thread and
delivers incremental entity changes to a listener. It is the recommended pattern for
continuously synchronising telemetry or entity state.

A minimal example is included in the
`examples/data_feed <https://github.com/Geotab/mygeotab-python/tree/main/examples/data_feed>`_
directory. See the API reference for the
:class:`DataFeed <mygeotab.ext.feed.DataFeed>` and
:class:`DataFeedListener <mygeotab.ext.feed.DataFeedListener>` classes.
