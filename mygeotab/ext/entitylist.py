# -*- coding: utf-8 -*-

import six
from mygeotab import api
from six.moves import UserList


class API(api.API):
    """An experimental wrapper around the base MyGeotab API class that adds some helper methods to results when
    retrieving results with `get()`.
    """

    def get(self, type_name, **parameters):
        """Gets entities using the API. Shortcut for using call() with the 'Get' method. This returns an EntityList
        with added convience methods.

        :param type_name: The type of entity.
        :type type_name: str
        :param parameters: Additional parameters to send.
        :raise MyGeotabException: Raises when an exception occurs on the MyGeotab server.
        :raise TimeoutException: Raises when the request does not respond after some time.
        :return: The results from the server.
        :rtype: EntityList
        """
        return EntityList(super().get(type_name, **parameters), type_name=type_name)


class EntityList(UserList):
    """The customized result list"""

    def __init__(self, data, type_name):
        """Gets entities using the API. Shortcut for using call() with the 'Get' method.

        :param data: The list of result data.
        :type data: list
        :param type_name: The type of entity.
        :type type_name: str
        """
        super(EntityList, self).__init__(data)
        self.type_name = type_name

    def _repr_pretty_(self, p, cycle):
        """The pretty printer for IPython"""
        if cycle:
            p.text("{}(...)".format(self.type_name))
        else:
            with p.group(8, "{}([".format(self.type_name), "])"):
                for idx, item in enumerate(self.data):
                    if idx:
                        p.text(",")
                        p.breakable()
                    p.pretty(item)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return self.__class__(self.data[i], self.type_name)
        else:
            return self.data[i]

    def __getslice__(self, i, j):
        i = max(i, 0)
        j = max(j, 0)
        return self.__class__(self.data[i:j], self.type_name)

    def __add__(self, other):
        if isinstance(other, UserList):
            return self.__class__(self.data + other.data, self.type_name)
        elif isinstance(other, type(self.data)):
            return self.__class__(self.data + other, self.type_name)
        return self.__class__(self.data + list(other), self.type_name)

    def __radd__(self, other):
        if isinstance(other, UserList):
            return self.__class__(other.data + self.data, self.type_name)
        elif isinstance(other, type(self.data)):
            return self.__class__(other + self.data, self.type_name)
        return self.__class__(list(other) + self.data, self.type_name)

    def __mul__(self, n):
        return self.__class__(self.data * n, self.type_name)

    __rmul__ = __mul__

    def __copy__(self):
        inst = self.__class__.__new__(self.__class__, self.type_name)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["data"] = self.__dict__["data"][:]
        return inst

    def sort_by(self, key, reverse=False):
        """Returns an EntityList, sorted by a provided key.

        :param key: The key to sort the data with.
        :type key: str
        :param reverse: If true, reverse the sort direction.
        :type reverse: bool
        :rtype: EntityList
        """

        def sort_by_key(entity):
            prop = entity[key]
            if isinstance(prop, six.string_types):
                return prop.lower()
            return prop

        return self.__class__(sorted(self.data, key=sort_by_key, reverse=reverse), type_name=self.type_name)

    @property
    def first(self):
        """Gets the first entity in the list, if it exists.

        :rtype: dict
        """
        return self.data[0] if self.data else None

    @property
    def last(self):
        """Gets the last entity in the list, if it exists.

        :rtype: dict
        """
        return self.data[-1] if self.data else None

    @property
    def entity(self):
        """Like `first`, but first asserts that there is only one entity in the results list.

        :rtype: dict
        """
        data_length = len(self.data)
        assert data_length == 1, "Expecting one entity, but {} entities were returned".format(data_length)
        return self.first

    def to_dataframe(self, normalize=False):
        """Transforms the data into a pandas DataFrame

        :param normalize: Whether or not to normalize any nested objects in the results into distinct columns.
        :type normalize: bool
        :rtype: pandas.DataFrame
        """
        try:
            import pandas
        except ImportError:
            raise ImportError("The 'pandas' package could not be imported")
        if normalize:
            try:
                return pandas.json_normalize(self.data)
            except AttributeError:
                from pandas.io.json import json_normalize

                return json_normalize(self.data)

        return pandas.DataFrame.from_dict(self.data)
