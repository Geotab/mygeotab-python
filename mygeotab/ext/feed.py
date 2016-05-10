# -*- coding: utf-8 -*-

import abc

from threading import Thread
from time import sleep


class DataFeedListener(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def on_data(self, data):
        """
        Called when rows of data are received

        :param data: A list of data objects
        """
        return

    @abc.abstractmethod
    def on_error(self, error):
        """
        Called when server errors are encountered. Return False to close the stream.

        :rtype: bool
        :param error: The error object
        :return: If True, keep listening. If False, stop the data feed.
        """
        return False


class DataFeed(object):
    def __init__(self, api, listener, type_name, interval, search=None):
        """
        A simple wrapper for the MyGeotab Data Feed. Create a listener that inherits
        from DataFeedListener to pass in.

        :param api: The MyGeotab API object
        :param listener: The custom DataFeedListener object
        :param type_name: The type of entity
        :param interval: The data retrieval interval (in seconds)
        :param search: The search object
        """
        self.api = api
        self.listener = listener
        self.type_name = type_name
        self.interval = interval
        self.search = search
        self.running = False
        self._version = None
        self._thread = None

    def _run(self):
        """
        Runner for the Data Feed

        """
        while self.running:
            try:
                result = self.api.call('GetFeed', type_name=self.type_name, search=self.search,
                                       from_version=self._version)
                self._version = result['toVersion']
                self.listener.on_data(result['data'])
            except Exception as e:
                if self.listener.on_error(e) is False:
                    break
            if not self.running:
                break
            sleep(self.interval)
        self.running = False

    def start(self, async=True):
        """
        Start the Data Feed

        :param async: If True, run in a separate thread
        """
        self.running = True
        if async:
            self._thread = Thread(target=self._run)
            self._thread.start()
        else:
            self._run()
