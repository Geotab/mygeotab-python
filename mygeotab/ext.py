# -*- coding: utf-8 -*-

from threading import Thread
from time import sleep


class DataFeedListener(object):
    def on_data(self, data):
        return

    def on_error(self, error):
        return False


class DataFeed(object):
    def __init__(self, api, listener, type_name, interval, search=None):
        self.api = api
        self.listener = listener
        self.type_name = type_name
        self.interval = interval
        self.search = search
        self.running = False
        self._version = None
        self._thread = None

    def _result(self, data):
        if self.listener.on_result(data) is False:
            self.running = False

    def _run(self):
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
        self.running = True
        if async:
            self._thread = Thread(target=self._run)
            self._thread.start()
        else:
            self._run()
