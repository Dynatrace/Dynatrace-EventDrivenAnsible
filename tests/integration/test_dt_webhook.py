"""Integration tests for dt_webhook.py."""
import asyncio
import json
from http import HTTPStatus

import aiohttp

# pylint: disable-next=import-error
import pytest

from extensions.eda.plugins.event_source.dt_webhook import main as dt_webhook

args = {
    "host": "127.0.0.1",
    "port": 1234,
    "token": "thisisnotanactualtoken",
}
url = f'http://{args["host"]}:{args["port"]}/event'
payload = json.dumps({"eventId": "1A2B3C"})
headers = {"Authorization": "Bearer " + args["token"]}


async def run_webhook() -> None:  # noqa: FA102, D103
    """Start webhook."""
    await dt_webhook(asyncio.Queue(), args)


@pytest.mark.asyncio
async def test_with_incorrect_path():
    """When posting data to an incorrect path, HTTP 404 Not Found should be returned"""
    async def do_request():
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f'http://{args["host"]}:{args["port"]}/something', data=payload) as resp:
                # task_cancel() stops the plugin coroutine which is wrapped into the task will never
                # stop and also the test will not be terminated.
                plugin_task.cancel()
                assert resp.status == HTTPStatus.NOT_FOUND

    plugin_task = asyncio.create_task(run_webhook())
    request_task = asyncio.create_task(do_request())
    await asyncio.gather(plugin_task, request_task)


@pytest.mark.asyncio
async def test_event_body_valid_json():
    """When posting valid JSON data, HTTP 200 OK with an empty JSON should be returned"""
    async def do_request():
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data=payload) as resp:
                plugin_task.cancel()
                text = await resp.text()
                assert resp.status == HTTPStatus.OK
                assert text == "{}"

    plugin_task = asyncio.create_task(run_webhook())
    request_task = asyncio.create_task(do_request())
    await asyncio.gather(plugin_task, request_task)


@pytest.mark.asyncio
async def test_event_body_with_invalid_json():
    """When posting invalid JSON data, HTTP 400 BAD REQUEST should be returned"""
    async def do_request():
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(url, data="this is no valid json") as resp:
                plugin_task.cancel()
                assert resp.status == HTTPStatus.BAD_REQUEST
                assert resp.reason == "Invalid JSON payload"

    plugin_task = asyncio.create_task(run_webhook())
    request_task = asyncio.create_task(do_request())
    await asyncio.gather(plugin_task, request_task)


@pytest.mark.asyncio
async def test_without_auth_header():
    """When posting data with incorrect Authorization header, HTTP 401 UNAUTHORIZED should be returned"""
    async def do_request():
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                plugin_task.cancel()
                assert resp.status == HTTPStatus.UNAUTHORIZED
                assert resp.reason == "Authorization header is missing or not correct"

    plugin_task = asyncio.create_task(run_webhook())
    request_task = asyncio.create_task(do_request())
    await asyncio.gather(plugin_task, request_task)
