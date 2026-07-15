Altitude
========

`Altitude <https://altitude.geotab.com/platform-overview/>`__ is Geotab's DaaS
(Data as a Service) platform. :class:`AltitudeAPI <mygeotab.altitude.wrapper.AltitudeAPI>`
is a subclass of :class:`API <mygeotab.API>` that routes all traffic through the
Altitude proxy endpoint.

Authentication works the same way as the core API — provide credentials and call
``authenticate()`` before making any data calls.

Workflow
--------

The typical Altitude workflow is:

1. **Submit** a query job with :func:`create_job() <mygeotab.altitude.wrapper.AltitudeAPI.create_job>`.
2. **Poll** until it finishes with :func:`wait_for_job_to_complete() <mygeotab.altitude.wrapper.AltitudeAPI.wait_for_job_to_complete>`.
3. **Retrieve** paginated results with :func:`get_data() <mygeotab.altitude.wrapper.AltitudeAPI.get_data>`.

The convenience method :func:`do() <mygeotab.altitude.wrapper.AltitudeAPI.do>` runs all
three steps in sequence:

.. code-block:: python

    from mygeotab.altitude.wrapper import AltitudeAPI

    api = AltitudeAPI(
        username='hello@example.com',
        password='mypass',
        database='MyDatabase',
    )
    api.authenticate()

    params = {
        'serviceName': 'MyService',
        'functionParameters': {
            'startDate': '2025-01-01T00:00:00Z',
            'endDate':   '2025-01-31T00:00:00Z',
        },
    }

    # All-in-one: submit → wait → fetch
    rows = api.do(params)

    # Or step-by-step for more control:
    job = api.create_job(params)
    params['functionParameters']['jobId'] = job['id']
    api.wait_for_job_to_complete(params)
    rows = api.get_data(params)

AltitudeAPI
-----------

.. autoclass:: mygeotab.altitude.wrapper.AltitudeAPI
   :members:
   :inherited-members:

Result Types
------------

.. autoclass:: mygeotab.altitude.daas_definition.DaasResult
   :members:

.. autoclass:: mygeotab.altitude.daas_definition.DaasGetJobStatusResult
   :members:

.. autoclass:: mygeotab.altitude.daas_definition.DaasGetQueryResult
   :members:

.. autoclass:: mygeotab.altitude.daas_definition.DaasError
   :members:
