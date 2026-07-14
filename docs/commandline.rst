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
pre-loaded with an authenticated API object:

.. code-block:: bash

    $ myg console my_database
    Username: my_user@example.com
    Password: ******
    Logged in as: my_user@example.com @ my1.geotab.com/my_database

Credentials can also be passed inline to skip the prompts:

.. code-block:: bash

    $ myg console my_database --user my_user@example.com --password mypass
    $ myg console my_database -u my_user@example.com -p mypass --server my3.geotab.com

Inside the console the following locals are available:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Name
     - Description
   * - ``myg``
     - The authenticated :class:`API <mygeotab.API>` object for the selected database.
   * - ``mygeotab``
     - The ``mygeotab`` module (for accessing exceptions, helpers, etc.).
   * - ``dates``
     - The :mod:`mygeotab.dates` module (date/timezone helpers).

.. code-block:: python

    >>> myg.get('Device', name='%Test%')
    >>> myg.call('GetVersion')

.. note::
    If ``ptpython`` or ``IPython`` is installed, the console launches with that
    instead of the standard Python REPL, providing syntax highlighting, tab
    completion, and pretty-printed output. Install either with ``pip install ptpython``
    or ``pip install ipython``.

    Once a database has been authenticated, ``myg`` remembers the session and
    won't prompt for credentials again until the session expires:

    .. code-block:: bash

        $ myg console my_database
        MyGeotab Console [Python 3.12.0]
        Logged in as: my_user@example.com @ my1.geotab.com/my_database

    If ``my_database`` was the last logged-in database, the argument can be omitted:

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
