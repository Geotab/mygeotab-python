Command Line Tools
==================

.. module:: mygeotab

The `myg` command line script is installed alongside this package, which currently makes some administration
and querying simple, as it handles the credential storage and token expiry automatically.

Currently, the script launches an interactive console to quickly query data from a database. More functionality
will be added in the future.

The tools never store passwords. The username, session token, and database are persisted and managed in
the local user's data directory.

Usage
-----

The most common usage of the `myg` script is to launch an interactive console.

For example, to launch a console for a database called `my_database`:

.. code-block:: bash

    $ myg console my_database
    Username: my_user
    Password: ******

.. note::
    The `myg` script automatically handles storing credentials for various databases and remembers the last logged in
    database. It also handles session expiry: it will prompt for a new password if the session has expired.

    For example, once the database has been authenticated against, the script won't prompt for passwords until the
    sesison expires:

    .. code-block:: bash

        $ myg console my_database
        MyGeotab Console 0.5.1 [Python 3.5.2 \|Anaconda custom (x86_64)\| (default, Jul  2 2016, 17:52:12) [GCC 4.2.1 Compatible Apple LLVM 4.2 (clang-425.0.28)]]
        Logged in as:  my_user @ my1.geotab.com/my_database
        In [1]:

    If `my_database` was the last logged in database, the following also works:

    .. code-block:: bash

        $ myg console

To view current sessions:

.. code-block:: bash

    $ myg sessions
    my_database
    my_other_database

And to remove a session:

.. code-block:: bash

    $ myg sessions remove my_database
    my_other_database

Additional Help
---------------

Run `--help` after any command to get available options and descriptions.

.. code-block:: bash

    $ myg --help
    $ myg console --help
