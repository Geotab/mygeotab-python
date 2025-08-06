# -*- coding: utf-8 -*-

import pytest
from mygeotab.parameters import camelcaseify_parameters, convert_get_parameters


def test_camelcaseify_parameters_basic():
    params = {"some_param": 1, "another_param": 2}
    result = camelcaseify_parameters(params)
    assert "someParam" in result
    assert "anotherParam" in result
    assert result["someParam"] == 1
    assert result["anotherParam"] == 2


def test_camelcaseify_parameters_nested():
    params = {"outer_param": {"inner_param": 3}}
    result = camelcaseify_parameters(params)
    assert "outerParam" in result
    assert isinstance(result["outerParam"], dict)
    assert "innerParam" in result["outerParam"]
    assert result["outerParam"]["innerParam"] == 3


def test_camelcaseify_parameters_empty():
    assert camelcaseify_parameters({}) == {}


def test_camelcaseify_parameters_no_underscore():
    params = {"param": 5}
    result = camelcaseify_parameters(params)
    assert "param" in result
    assert result["param"] == 5


def test_convert_get_parameters_with_search_and_results_limit():
    params = {"search": {"foo": "bar"}, "results_limit": 10}
    result = convert_get_parameters(params)
    assert "search" in result
    assert result["search"]["foo"] == "bar"
    assert "resultsLimit" in result
    assert result["resultsLimit"] == 10


def test_convert_get_parameters_with_search_and_resultsLimit():
    params = {"search": {"foo": "bar"}, "resultsLimit": 5}
    result = convert_get_parameters(params)
    assert "search" in result
    assert result["search"]["foo"] == "bar"
    assert "resultsLimit" in result
    assert result["resultsLimit"] == 5


def test_convert_get_parameters_flatten_search():
    params = {"search": {"foo": "bar", "baz": 2}}
    result = convert_get_parameters(params)
    assert "search" in result
    assert result["search"]["foo"] == "bar"
    assert result["search"]["baz"] == 2


def test_convert_get_parameters_no_search():
    params = {"foo": "bar", "resultsLimit": 3}
    result = convert_get_parameters(params)
    assert "search" in result
    assert result["search"]["foo"] == "bar"
    assert "resultsLimit" in result
    assert result["resultsLimit"] == 3


def test_convert_get_parameters_empty():
    assert convert_get_parameters({}) == {}


def test_convert_get_parameters_removes_results_limit_from_search():
    params = {"search": {"foo": "bar"}, "results_limit": 7}
    result = convert_get_parameters(params)
    assert "resultsLimit" in result
    assert result["resultsLimit"] == 7
    assert "results_limit" not in result["search"]


def test_convert_get_parameters_with_sort():
    params = {
        "search": {"foo": "bar"},
        "sort": {"sortBy": "name", "sortDirection": "asc", "offset": "Delivery Truck 12", "lastId": "b1234"},
    }
    result = convert_get_parameters(params)
    assert "sort" in result
    assert isinstance(result["sort"], dict)
    assert result["sort"]["sortBy"] == "name"
    assert result["sort"]["sortDirection"] == "asc"
    assert result["sort"]["offset"] == "Delivery Truck 12"
    assert result["sort"]["lastId"] == "b1234"


def test_convert_get_parameters_with_property_selector():
    params = {"search": {"foo": "bar"}, "propertySelector": {"fields": ["id", "name"], "isIncluded": True}}
    result = convert_get_parameters(params)
    assert "propertySelector" in result
    assert isinstance(result["propertySelector"], dict)
    assert "fields" in result["propertySelector"]
    assert "isIncluded" in result["propertySelector"]


def test_convert_get_parameters_with_property_selector_snake_case():
    params = {"search": {"foo": "bar"}, "property_selector": {"fields": ["id", "name"], "isIncluded": True}}
    result = convert_get_parameters(params)
    assert "propertySelector" in result
    assert isinstance(result["propertySelector"], dict)
    assert "fields" in result["propertySelector"]
    assert "isIncluded" in result["propertySelector"]


def test_convert_get_parameters_with_sort_and_property_selector():
    params = {
        "search": {"foo": "bar"},
        "sort": {"sortBy": "name", "sortDirection": "asc", "offset": "Delivery Truck 12", "lastId": "b1234"},
        "property_selector": {"fields": ["id", "status"], "isIncluded": True},
    }
    result = convert_get_parameters(params)
    assert "sort" in result
    assert result["sort"]["sortBy"] == "name"
    assert result["sort"]["sortDirection"] == "asc"
    assert result["sort"]["offset"] == "Delivery Truck 12"
    assert result["sort"]["lastId"] == "b1234"
    assert "propertySelector" in result
    assert "fields" in result["propertySelector"]
    assert "isIncluded" in result["propertySelector"]
