# -*- coding: utf-8 -*-

from collections import defaultdict

import click

from mygeotab import API, dates
from mygeotab.ext import feed


class ExceptionDataFeedListener(feed.DataFeedListener):
    def __init__(self, api):
        """
        A simple Data Feed listener for Exception Event data

        :param api: The MyGeotab API object
        """
        self.api = api
        self._cache = defaultdict(dict)
        super(feed.DataFeedListener, self).__init__()

    def _populate_sub_entity(self, entity, type_name):
        """
        Simple API-backed cache for populating MyGeotab entities

        :param entity: The entity to populate a sub-entity for
        :param type_name: The type of the sub-entity to populate
        """
        key = type_name.lower()
        if isinstance(entity[key], str):
            # If the expected sub-entity is a string, it's a unknown ID
            entity[key] = dict(id=entity[key])
            return
        cache = self._cache[key]
        subentity = cache.get(entity[key]["id"])
        if not subentity:
            subentities = self.api.get(type_name, id=entity[key]["id"], results_limit=1)
            if len(subentities) > 0:
                subentity = subentities[0]
                entity[key] = subentity
        else:
            entity[key] = subentity

    def on_data(self, data):
        """
        The function called when new data has arrived.

        :param data: The list of data records received.
        """
        for d in data:
            self._populate_sub_entity(d, "Device")
            self._populate_sub_entity(d, "Rule")
            date = dates.localize_datetime(d["activeFrom"])
            click.echo(
                "[{date}] {device} ({rule})".format(
                    date=date,
                    device=d["device"].get("name", "**Unknown Vehicle"),
                    rule=d["rule"].get("name", "**Unknown Rule"),
                )
            )

    def on_error(self, error):
        """
        The function called when an error has occurred.

        :rtype: bool
        :param error:
        :return: If True, keep listening. If False, stop the data feed.
        """
        click.secho(error, fg="red")
        return True


@click.command(help="A console data feeder example")
@click.argument("database", nargs=1, required=True)
@click.option("--user", "-u", prompt=True, help="A MyGeotab username")
@click.option("--password", "-p", prompt=True, hide_input=True, help="A MyGeotab password")
@click.option("--server", default=None, help="The server (default is my.geotab.com)")
@click.option(
    "--interval",
    "-i",
    type=click.IntRange(5, 300),
    default=60,
    help="The data feed interval in seconds (default is 60 seconds)",
)
def main(database, user=None, password=None, server=None, interval=60):
    api = API(database=database, username=user, password=password, server=server)
    api.authenticate()
    feed.DataFeed(api, ExceptionDataFeedListener(api), "ExceptionEvent", interval=interval).start()


if __name__ == "__main__":
    main()
