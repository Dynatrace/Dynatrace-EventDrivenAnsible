"""Plugin pulls Dynatrace detected problems and sends it to the EDA server."""
from __future__ import annotations

import asyncio
import logging
from http import HTTPStatus
from typing import Any

# pylint: disable-next=import-error
import aiohttp

PROBLEM_QUERY_TIME = 10


def get_client_session(dtapitoken: str) -> aiohttp.ClientSession:
    timeout = aiohttp.ClientTimeout(total=30)
    return aiohttp.ClientSession(
        headers={"Authorization": f"Api-Token {dtapitoken}"},
        timeout=timeout,
        raise_for_status=True,
    )


async def get_problems(session: aiohttp.ClientSession, dt_host: str, proxy: str) -> None:
    """Pull Dynatrace detected problems from Dynatrace Problems API.

    Parameters
    ----------
    session : aiohttp.ClientSession
        ClientSession with Auth header and timeout
    dt_host : str
        Dynatrace host.
    proxy: str
        Proxy through which to access host.

    Returns
    -------
    Response.

    """
    url = f"{dt_host}/api/v2/problems?fields=recentComments&from=now-{PROBLEM_QUERY_TIME}m&to=now"
    try:
        async with session.get(url=url, proxy=proxy) as resp:
            return await resp.json()
    except aiohttp.ClientResponseError:
        logging.exception("Exception in response from Dynatrace API")
    except aiohttp.ClientConnectionError:
        logging.exception("Exception connecting to Dynatrace API")
    except aiohttp.ClientError:
        logging.exception("aiohttp client Exception")


async def update_problem(session: aiohttp.ClientSession, prob_id: str, dtapihost: str,
                         proxy: str) -> None:
    """Update problem comment once its sent to the EDA server.

    Parameters
    ----------
    session : aiohttp.ClientSession
        ClientSession with Auth header and timeout
    prob_id : str
        Problem ID.
    dtapihost : str
        Host to query.
    proxy: str
        Proxy through which to access host.

    """
    url = f"{dtapihost}/api/v2/problems/{prob_id}/comments"
    commentbody = {}
    commentbody["context"] = "Event Driven Ansible"
    commentbody["message"] = "Sent to EDA Server"
    try:
        resp = await session.post(url, json=commentbody, proxy=proxy)
        if resp.status != HTTPStatus.CREATED:
            logging.warning(resp.status)
            logging.warning(resp.text)
    except aiohttp.ClientResponseError:
        logging.exception("Exception in response from Dynatrace API")
    except aiohttp.ClientConnectionError:
        logging.exception("Exception connecting to Dynatrace API")
    except aiohttp.ClientError:
        logging.exception("aiohttp client Exception")


def is_problem_in_eda(problem):
    pr_comment = problem.get("recentComments").get("comments")
    for comm in pr_comment:
        contents = comm["content"]
        if "EDA" in contents:
            return True
    return False


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Process the problem information.

    Parameters
    ----------
    queue : asyncio.Queue
        Problem queue.
    args : Dict[str,Any])
        Args containing the host and API access token.

    """
    logging.info("dt_esa_api plugin started")
    dt_api_host = args.get("dt_api_host")
    dt_api_token = args.get("dt_api_token")
    delay = int(args.get("delay", 60))
    proxy = args.get("proxy", "")

    if delay >= 60 * PROBLEM_QUERY_TIME:
        logging.error("The delay cannot be longer than 10 minutes" +
                      " because it would exceed the timespan for which the problems are retrieved")
        return

    try:
        session = get_client_session(dt_api_token)
        while True:
            problems = await get_problems(session, dt_api_host, proxy)
            if problems is not None:
                for problem in problems.get("problems"):
                    display_id = problem.get("displayId")
                    if is_problem_in_eda(problem):
                        logging.debug(f"Problem {display_id} has already been sent to EDA")
                    else:
                        prob_id = problem.get("problemId")
                        await queue.put(problem)
                        logging.debug(f"New Problem {display_id} added to EDA queue")
                        # Once sent update comment to "Sent to EDA server"
                        await update_problem(session, prob_id, dt_api_host, proxy)
            await asyncio.sleep(delay)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logging.exception("Async request timed out or cancelled")
