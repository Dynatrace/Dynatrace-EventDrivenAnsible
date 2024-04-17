"""Unit tests for dt_webhook.py."""
# pylint: disable-next=import-error
import pytest
from aiohttp import web

from extensions.eda.plugins.event_source.dt_webhook import (
    _parse_auth_header,
    _set_app_attributes,
)

args = {
    "host": "127.0.0.1",
    "port": 1234,
    "token": "thisisnotanactualtoken",
}


def test_parse_token_with_incorrect_token():
    with pytest.raises(web.HTTPUnauthorized, match="Invalid authorization token"):
        _parse_auth_header("Bearer", "thisisnotanactualtoken!", args["token"])


def test_parse_token_invalid_auth_type():
    with pytest.raises(web.HTTPUnauthorized, match="Authorization type Token is not allowed"):
        _parse_auth_header("Token", "thisisnotanactualtoken!", args["token"])


def test_set_app_attributes():
    app_attrs = _set_app_attributes(args)
    assert app_attrs["host"] == "127.0.0.1"
    assert app_attrs["port"] == 1234
    assert app_attrs["token"] == "thisisnotanactualtoken"


def test_set_app_attributes_without_port():
    with pytest.raises(ValueError, match="Port is missing as an argument"):
        _set_app_attributes({
            "host": "127.0.0.1",
            "token": "thisisnotanactualtoken",
        })


def test_set_app_attributes_without_host():
    with pytest.raises(ValueError, match="Host is missing as an argument"):
        _set_app_attributes({
            "port": "1234",
            "token": "thisisnotanactualtoken",
        })


def test_set_app_attributes_without_token():
    with pytest.raises(ValueError, match="Token is missing as an argument"):
        _set_app_attributes({
            "host": "127.0.0.1",
            "port": "1234",
        })
