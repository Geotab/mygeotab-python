# -*- coding: utf-8 -*-

"""
mygeotab.exceptions
~~~~~~~~~~~~~~~~~~~

Exceptions thrown by the MyGeotab API.
"""


class MyGeotabException(IOError):
    """There was an exception while handling your call."""

    def __init__(self, full_error, *args, **kwargs):
        """Initialize MyGeotabException with the full error from the server.

        :param full_error: The full JSON-decoded error.
        """
        self._full_error = full_error
        main_error = full_error["errors"][0]
        self.name = main_error["name"]
        self.message = main_error["message"]
        self.data = main_error.get("data")
        self.stack_trace = main_error.get("stackTrace")
        super(MyGeotabException, self).__init__(self.message, *args, **kwargs)

    def __str__(self):
        error_str = "{0}\n{1}".format(self.name, self.message)
        if self.stack_trace:
            error_str += "\n\nStacktrace:\n{0}".format(self.stack_trace)
        return error_str


class AuthenticationException(IOError):
    """Unsuccessful authentication with the server."""

    def __init__(self, username, database, server, *args, **kwargs):
        """Initialize AuthenticationException with username, database, and server.

        :param username: The username used for MyGeotab servers. Usually an email address.
        :param database: The database or company name.
        :param server: The server ie. my23.geotab.com.
        """
        self.username = username
        self.database = database
        self.server = server
        super(AuthenticationException, self).__init__(self.message, *args, **kwargs)

    def __str__(self):
        return self.message

    @property
    def message(self):
        """The exception message."""
        return "Cannot authenticate '{0} @ {1}/{2}'".format(self.username, self.server, self.database)


class TimeoutException(IOError):
    """The request timed out while handling your request."""

    def __init__(self, server, *args, **kwargs):
        """Initialize TimeoutException with the server name.

        :param server: The server ie. my23.geotab.com.
        """
        self.server = server
        super(TimeoutException, self).__init__(self.message, *args, **kwargs)

    def __str__(self):
        return self.message

    @property
    def message(self):
        """The excepton message."""
        return "Request timed out @ {0}".format(self.server)
