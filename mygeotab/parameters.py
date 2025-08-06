# -*- coding: utf-8 -*-

"""
mygeotab.parameters
~~~~~~~~~~~~~~~~~~~

This module contains parameter utilities used in the MyGeotab API.
"""

import re
from copy import copy
from typing import Any


def camelcaseify_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Allows the use of Pythonic-style parameters with underscores instead of camel-case.

    :param parameters: The parameters object.
    :type parameters: dict
    :return: The processed parameters.
    :rtype: dict
    """
    if not parameters:
        return dict()
    params = copy(parameters)
    for param_name in parameters:
        value = parameters[param_name]
        server_param_name = re.sub(r"_(\w)", lambda m: m.group(1).upper(), param_name)
        if isinstance(value, dict):
            value = camelcaseify_parameters(value)
        params[server_param_name] = value
        if server_param_name != param_name:
            del params[param_name]
    return params


def convert_get_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Converts parameters passed into a get() call to a format suitable for the MyGeotab API.
    It detects if a 'search' dictionary is passed and flattens it into the top-level parameters.
    It also detects 'resultsLimit' or 'results_limit' and removes it from the parameters
    so it doesn't become part of the search.

    :param parameters: The parameters object.
    :type parameters: dict
    :return: The processed parameters.
    :rtype: dict
    """
    if not parameters:
        return dict()

    results_limit = parameters.get("resultsLimit")
    if results_limit is not None:
        del parameters["resultsLimit"]
    else:
        results_limit = parameters.get("results_limit")
        if results_limit is not None:
            del parameters["results_limit"]

    if "search" in parameters:
        parameters.update(parameters["search"])
        del parameters["search"]
    result = {"search": parameters}
    if results_limit is not None:
        result["resultsLimit"] = results_limit
    return result
