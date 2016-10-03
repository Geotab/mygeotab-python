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