Usage
=====

.. module:: mygeotab

Getting Started
---------------

For a quick introduction to the MyGeotab SDK and initial setup of a database,
please refer to the `Getting Started guide <https://my.geotab.com/sdk/#/gettingStarted>`_.

For an overview of some basic concepts, the `Concepts guide <https://my.geotab.com/sdk/#/concepts>`_
is a good resource to find out how things work under the hood.

Authentication
--------------

The first step is to authenticate with a MyGeotab database. Import the library and create an :class:`API <mygeotab.API>`
object:

.. code-block:: python

    import mygeotab
    api = mygeotab.API(username='hello@example.com', password='mypass', database='DemoDB')
    api.authenticate()


.. note::
    If the intended purpose for this SDK application is for an end-user service where they can log in, consider catching the :class:`AuthenticationException <mygeotab.AuthenticationException>` and handle it
    (ex. displaying an error message to the user):

    .. code-block:: python

        try:
            api.authenticate()
        except mygeotab.AuthenticationException as ex:
            # Handle authentication issues here
            print(ex) # Cannot authenticate 'hello@example.com @ my.geotab.com/DemoDb'


To handle the saving of credentials for later use (a Geotab best practices recommendation), the :func:`authenticate() <mygeotab.API.authenticate>` method returns an instance of the :class:`Credentials <mygeotab.Credentials>` object.
From this, store the `database`, `username`, and `session_id` properties so they can be used later:

.. code-block:: python

    credentials = api.authenticate()
    my_save_credentials(username=credentials.username, database=credentials.database, session_id=credentials.session_id)

    # Continue with api object until your app finishes

    local_credentials = my_read_credentials() # Next load of the app
    new_api = mygeotab.api(username=local_credentials.user, database=local_credentials.database, session_id=saved_session_id)

.. note::
    The best practices of saving credentials only applies to some service-based SDK apps. The recommendation is that if the app runs on
    a schedule (for example, a operating system-scheduled task running every minute), store the credentials locally.

    Too many authentication attempts within a period of time will cause the server to reject any further requests for a short time.

    However, constantly running sessions may not need to store the credentials in the file system as they can retain the :class:`API <mygeotab.API>`
    instance in memory.

Making Calls
------------

At the core of every interaction with the MyGeotab API is the :func:`call() <mygeotab.API.call>` method, which executes a secure HTTPS
call to the MyGeotab server.

The most basic call is to get the version of MyGeotab that the server is running, which doesn't take any parameters:

.. code-block:: python

    api.call('GetVersion')
    # '5.7.1610.229'

To demonstrate a (slightly) more complex call with 1 parameter, the following is a query for all the vehicles in a database.

Assume for this example there is one vehicle in the system, with a partial JSON representation:

.. code-block:: javascript

    {
        "id": "b0a46",
        "name": "007 - Aston Martin",
        "serialNumber": "GTA9000003EA",
        "deviceType": "GO6",
        "vehicleIdentificationNumber": "1002",
        ...
    }

Get a list of all the vehicles by using:

.. code-block:: python

    api.call('Get', typeName='Device')

To filter this down to a specific vehicle, a 'search' parameter is added on the serial number of the GO device:

.. code-block:: python

    api.call('Get', typeName='Device', search={'serialNumber': 'GTA9000003EA'})

.. note::
    In this Python library, a lot of effort was made to make this a much easier experience. Please read the below section
    to see how the above call was made to be more Pythonic and easier to use.

For more information on calls available, visit the "Methods" section of the `MyGeotab API Reference <https://my.geotab.com/sdk/#/api>`_.

Entities
--------

From the `MyGeotab API Concepts documentation <https://my.geotab.com/sdk/#/concepts>`_:

.. pull-quote::
    All objects in the MyGeotab system are called entities. Entities have an ID property that is used to uniquely identify that object in the database.

There are several helper methods added in this SDK library that do some wrapping around the :func:`call() <mygeotab.API.call>` method to make it more Pythonic
and easier to work with.

To re-use the above example vehicle of getting all vehicles:

.. code-block:: python

    api.call('Get', typeName='Device')

A :func:`get() <mygeotab.API.get>` method was introduced, so it could be written as such:

.. code-block:: python

    api.get('Device')

And in a similar fashion, the call for the vehicle with the specified serial number:

.. code-block:: python

    api.call('Get', typeName='Device', search={'serialNumber': 'GTA9000003EA'})

The "search" parameter was abstracted out, so that it could be written as:

.. code-block:: python

    api.get('Device', serialNumber='GTA9000003EA')

