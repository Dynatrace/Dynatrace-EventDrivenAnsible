# ruff: noqa: FA102
"""dt_webhook.py.

Description:
This is an event source plugin for receiving events via a webhook
from the "send-event-to-eda" action of Dynatrace Workflows.
The payload must be a valid JSON object.

Arguments:
---------
  - host:     The hostname to listen to
  - port:     The TCP port to listen to
  - token:    The authentication token expected from Dynatrace

Usage in a rulebook:
- name: Watch for new events
  hosts: localhost
  sources:
    - dynatrace.event_driven_ansible.dt_webhook:
            host: 0.0.0.0
            port: 5000
            token: <your-token>

  rules:
    - name: API Endpoint not available
      condition: event.payload.eventData["event.name"] contains "Endpoint not available"
      action:
        run_job_template:
          name: "Run my job template"
          organization: "Default"

"""
import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

# pylint: disable-next=import-error
from aiohttp import web

logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


# initialize loggger configuration
def _initialize_logger_config() -> None:
    logging.basicConfig(
        format="[%(asctime)s] - %(pathname)s: %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %I:%M:%S",
    )


# request handler for incoming events
@routes.post("/event")
async def handle_event(request: web.Request) -> web.Response:
    """Handle received event and put it on the queue.

    Parameters
    ----------
    request : web.Request
        Received request.

    Returns
    -------
    Response with empty JSON object.

    Raises
    ------
    HTTPBadRequest
        If the payload can't be parsed as JSON.

    """
    logger.info("Received event")
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        logger.exception("Failed to parse JSON payload: %s")
        raise web.HTTPBadRequest(reason="Invalid JSON payload") from None
    headers = dict(request.headers)
    headers.pop("Authorization", None)
    data = {
        "payload": payload,
        "meta": {"headers": headers},
    }
    logger.info("Put event on queue")
    await request.app["queue"].put(data)
    return web.json_response({})


def _parse_auth_header(scheme: str, token: str, configured_token: str) -> None:
    """Check authorization type and token.

    Parameters
    ----------
    scheme : str
        Authorization schema from request header.
    token : str
        Token string retrieved from request header.
    configured_token : str
        Token string retrieved from args.

    Raises
    ------
    HTTPUnauthorized
        If the authorization type is not allowed or token is invalid

    """
    if scheme != "Bearer":
        msg = f"Authorization type {scheme} is not allowed"
        logger.error(msg)
        raise web.HTTPUnauthorized(reason=msg) from None
    if token != configured_token:
        msg = "Invalid authorization token"
        logger.error(msg)
        raise web.HTTPUnauthorized(reason=msg) from None


@web.middleware
async def check_auth(request: web.Request, handler: Callable) -> web.StreamResponse:
    """Check authorization header.

    Parameters
    ----------
    request : web.Request
        Received request.
    handler : Callable
        Request handler
        https://docs.aiohttp.org/en/stable/web_quickstart.html#aiohttp-web-handler

    Returns
    -------
    StreamResponse
        https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.StreamResponse

    Raises
    ------
    HTTPUnauthorized
        If the authorization type is not allowed or token is invalid

    """
    try:
        scheme, token = request.headers["Authorization"].strip().split(" ")
        _parse_auth_header(scheme, token, request.app["token"])
    except KeyError:
        msg = "Authorization header is missing or not correct"
        logger.exception(msg)
        raise web.HTTPUnauthorized(reason=msg) from None
    except ValueError:
        msg = "Invalid authorization header"
        logger.exception(msg)
        raise web.HTTPUnauthorized(reason=msg) from None
    return await handler(request)


def _set_app_attributes(args: dict[str, Any]) -> dict[str, Any]:
    if "host" not in args:
        msg = "Host is missing as an argument"
        logger.error(msg)
        raise ValueError(msg)

    if "port" not in args:
        msg = "Port is missing as an argument"
        logger.error(msg)
        raise ValueError(msg)

    if "token" not in args:
        msg = "Token is missing as an argument"
        logger.error(msg)
        raise ValueError(msg)

    app_attrs = {}
    app_attrs["host"] = args.get("host")
    app_attrs["port"] = args.get("port")
    app_attrs["token"] = args.get("token")

    return app_attrs


# Entrypoint from ansible-rulebook
async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Entrypoint from ansible-rulebook cli.

    Parameters
    ----------
    queue : asyncio.Queue
        Problem queue.
    args : Dict[str,Any])
        Args containing the host, port and access token.

    """
    _initialize_logger_config()
    logging.info("Starting dt_webhook...")

    app_attrs = _set_app_attributes(args)
    app = web.Application(middlewares=[check_auth])
    app.add_routes(routes)

    # store queue and token in app config to access it in the web-handler and middleware
    app["queue"] = queue
    app["token"] = app_attrs["token"]

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        app_attrs["host"],
        app_attrs["port"],
    )
    await site.start()
    logger.info("dt_webhook is running and waiting for events")

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Webhook plugin stopped due to an error")
    finally:
        await runner.cleanup()
