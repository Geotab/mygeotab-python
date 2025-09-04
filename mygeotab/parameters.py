# -*- coding: utf-8 -*-

"""
mygeotab.parameters
~~~~~~~~~~~~~~~~~~~

This module contains parameter utilities used in the MyGeotab API.
"""

import re
from copy import copy
from typing import Any, Optional, Dict, Union


def camelcaseify_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
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


def convert_get_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Converts parameters passed into a get() call to a format suitable for the MyGeotab API.
    It detects if a 'search' dictionary is passed and flattens it into the top-level parameters.
    It also detects 'resultsLimit'/'results_limit' or 'sort' parameters and removes them from the parameters
    so they doesn't become part of the search.

    :param parameters: The parameters object.
    :type parameters: dict
    :return: The processed parameters.
    :rtype: dict
    """
    if not parameters:
        return dict()

    parameters = copy(parameters)

    results_limit_param = _try_extract_get_parameter(parameters, "resultsLimit", "results_limit")
    property_selector_param = _try_extract_get_parameter(parameters, "propertySelector", "property_selector")
    sort_param = _try_extract_get_parameter(parameters, "sort")

    if "search" in parameters:
        parameters.update(parameters["search"])
        del parameters["search"]

    result = {"search": parameters}
    if results_limit_param is not None:
        result["resultsLimit"] = results_limit_param
    if property_selector_param is not None:
        result["propertySelector"] = property_selector_param
    if sort_param is not None:
        result["sort"] = sort_param
    return result


def _try_extract_get_parameter(parameters: Dict[str, Any], name: str, pythonic_name: Optional[str] = None) -> Union[Any, None]:
    """Helper to get a parameter from a dictionary, returning None if it doesn't exist."""
    parameter = parameters.get(name)
    if parameter is not None:
        del parameters[name]
    elif pythonic_name is not None:
        parameter = parameters.get(pythonic_name)
        if parameter is not None:
            del parameters[pythonic_name]
    return parameter
