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

If the intended purpose for this SDK application is for an end-user service where they can log in, consider catching the :class:`AuthenticationException <mygeotab.AuthenticationException>` and handle it
(ex. displaying an error message to the user):

.. code-block:: python

    try:
        api.authenticate()
    except mygeotab.AuthenticationException as ex:
        # Handle authentication issues here
        print(ex) # Cannot authenticate 'hello@example.com @ my.geotab.com/DemoDb'
