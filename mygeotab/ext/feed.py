# -*- coding: utf-8 -*-

"""
mygeotab.ext.feed
~~~~~~~~~~~~~~~~~

A simple data feed wrapper, written as an extension to the MyGeotab API object.
"""

import abc
from threading import Thread
from time import sleep

from mygeotab import api
from requests.exceptions import ConnectionError


class DataFeedListener(object):
    """The abstract DataFeedListener to override"""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def on_data(self, data):
        """Called when rows of data are received.

        :param data: A list of data objects.
        """
        return

    @abc.abstractmethod
    def on_error(self, error):
        """Called when server errors are encountered. Return False to close the stream.

        :rtype: bool
        :param error: The error object.
        :return: If True, keep listening. If False, stop the data feed.
        """
        return False


class DataFeed(object):
    """A simple wrapper for the MyGeotab Data Feed. Create a listener that inherits
    from DataFeedListener to pass in.
    """

    def __init__(self, client_api, listener, type_name, interval, search=None, results_limit=None):
        """Initializes the DataFeed object.

        :param client_api: The MyGeotab API object.
        :param listener: The custom DataFeedListener object.
        :param type_name: The type of entity.
        :param interval: The data retrieval interval (in seconds).
        :param search: The search object.
        :param results_limit: The maximum number of records to return.
        """
        self.client_api = client_api
        self.listener = listener
        self.type_name = type_name
        self.interval = interval
        self.search = search
        self.results_limit = results_limit
        self.running = False
        self._version = None
        self._thread = None

    def _run(self):
        """Runner for the Data Feed."""
        while self.running:
            try:
                result = self.client_api.call(
                    "GetFeed",
                    type_name=self.type_name,
                    search=self.search,
                    from_version=self._version,
                    results_limit=self.results_limit,
                )
                self._version = result["toVersion"]
                self.listener.on_data(result["data"])
            except (api.MyGeotabException, ConnectionError) as exception:
                if self.listener.on_error(exception) is False:
                    break
            if not self.running:
                break
            sleep(self.interval)
        self.running = False

    def start(self, threaded=True):
        """Start the data feed.

        :param threaded: If True, run in a separate thread.
        """
        self.running = True
        if threaded:
            self._thread = Thread(target=self._run)
            self._thread.start()
        else:
            self._run()
