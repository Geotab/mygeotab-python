# -*- coding: utf-8 -*-

import click

from mygeotab import ext, API, dates


class ExceptionDataFeedListener(ext.DataFeedListener):
    def __init__(self, api):
        """
        A simple Data Feed listener for ExceptionEvent data

        :param api: The MyGeotab API object
        """
        self.api = api
        self._devices = {}
        super(ext.DataFeedListener, self).__init__()

    def on_data(self, data):
        for d in data:
            device = self._devices.get(d['device']['id'])
            if not device:
                devices = self.api.search('Device', id=d['device']['id'], results_limit=1)
                if len(devices) > 0:
                    device = devices[0]
                    self._devices[device['id']] = device
                else:
                    device = d['device']
            date = dates.localize_datetime(d['activeFrom'])
            click.echo('[{0}] {1}'.format(date, device.get('name', '**Unknown Vehicle')))

    def on_error(self, error):
        click.secho(error, fg='red')


@click.command(help="A console data feeder example")
@click.argument('database', nargs=1, required=False)
@click.option('--user', '-u', prompt=True)
@click.option('--password', '-p', prompt=True, hide_input=True)
@click.option('--server', default=None, help='The server (ie. my4.geotab.com)')
@click.option('--interval', '-i', type=click.IntRange(5, 300))
def main(database=None, user=None, password=None, server=None, interval=60):
    api = API(database=database, username=user, password=password, server=server)
    api.authenticate()
    ext.DataFeed(api, ExceptionDataFeedListener(api), 'ExceptionEvent', interval=interval).start()


if __name__ == '__main__':
    main()
