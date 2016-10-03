Command Line Tools
==================

.. module:: mygeotab

The `myg` command line script is installed alongside this package, which currently makes some administration
and querying simple, as it handles the credential storage and token expiry automatically.

Currently, the script handles running either:

- An interactive console to quickly query data from a database
- A script "runner" that can run a simple Python-based tasks

The tools never store passwords. The username, session token, and database are persisted and managed in
the local user's data directory.

Usage
-----

Coming soon. For now, run:

.. code-block:: bash

    $ myg --help

to view the latest documentation for `myg`.
