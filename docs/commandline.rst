Command Line Tools
==================

The ``myg`` command-line tool is installed alongside this package. It handles
credential storage and session token expiry automatically, so you can focus on
querying data rather than managing authentication boilerplate.

.. note::
    ``myg`` never stores passwords. Only the username, database name, server,
    and session token are persisted. The config file and its parent directory
    are created with owner-only permissions (``0700``/``0600``) so other local
    users cannot read your session tokens.

    To clear a saved session at any time, run ``myg sessions remove <database>``.

Usage
-----

Launching a console
~~~~~~~~~~~~~~~~~~~

The most common use of ``myg`` is to open an interactive Python console
pre-loaded with an authenticated API object (``myg``):

.. code-block:: bash

    $ myg console my_database
    Username: my_user@example.com
    Password: ******
    Logged in as: my_user@example.com @ my1.geotab.com/my_database

Inside the console, use ``myg`` to make API calls:

.. code-block:: python

    >>> myg.get('Device', name='%Test%')
    >>> myg.call('GetVersion')

.. note::
    Once a database has been authenticated, ``myg`` remembers the session and
    won't prompt for credentials again until the session expires:

    .. code-block:: bash

        $ myg console my_database
        MyGeotab Console 0.9.7 [Python 3.12.0]
        Logged in as: my_user@example.com @ my1.geotab.com/my_database

    If ``my_database`` was the last logged-in database, the database argument
    can be omitted:

    .. code-block:: bash

        $ myg console

Managing sessions
~~~~~~~~~~~~~~~~~

List all saved sessions:

.. code-block:: bash

    $ myg sessions --list
    my_database
    my_other_database

Remove a session (logs out and deletes the stored token):

.. code-block:: bash

    $ myg sessions remove my_database
    my_other_database

Additional Help
---------------

Run ``--help`` after any command to see all available options:

.. code-block:: bash

    $ myg --help
    $ myg console --help
    $ myg sessions --help
