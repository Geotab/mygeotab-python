Data Feed Example for Exception Events
======================================

A simple example Data Feed listener for Exception Event data.

Running
-------

To run:

.. code-block:: bash

    $ python feeder.py abc_company_database

The prompt will ask for your MyGeotab username and password.

By default, this will poll every 10 seconds for data. To change this,
pass in the amount of seconds to the ``i`` parameter:

.. code-block:: bash

    $ python feeder.py abc_company_database -i 20

For more options and help, use:

.. code-block:: bash

    $ python feeder.py --help
