"""Plugin pulls Dynatrace detected problems and sends it to the EDA server."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

# pylint: disable-next=import-error
import aiohttp


async def getproblems(dt_host: str, dt_token: str) -> None:
    """Pull Dynatrace detected problems from Dynatrace Problems API.

    Parameters
    ----------
    dt_host : str
        Dynatrace host.
    dt_token : str
        Dynatrace access token.

    Returns
    -------
    Response.
    """
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Api-Token {dt_token}"},
        timeout=timeout,
        raise_for_status=True,
    ) as session:
        url = f"{dt_host}/api/v2/problems?fields=recentComments&from=now-10m&to=now"
        async with session.get(url) as resp:
            try:
                return await resp.json()
            except aiohttp.ClientResponseError:
                logging.exception("Exception in response from Dynatrace API")
            except aiohttp.ClientConnectionError:
                logging.exception("Exception connecting to Dynatrace API")
            except aiohttp.ClientError:
                logging.exception("aiohttp client Exception")


async def updatedtproblem(prob_id: str, dtapihost: str, dtapitoken: str) -> None:
    """Update problem comment once its sent to the EDA server.

    Parameters
    ----------
    prob_id : str
        Problem ID.
    dtapihost : str
        Host to query.
    dtapitoken: str
        Host API token.

    """
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Api-Token {dtapitoken}"},
        timeout=timeout,
        raise_for_status=True,
    ) as session:
        url = f"{dtapihost}/api/v2/problems/{prob_id}/comments"
        commentbody = {}
        commentbody["context"] = "Event Driven Ansible"
        commentbody["message"] = "Sent to EDA Server"
        try:
            resp = await session.post(url, json=commentbody)
            warning_status = 201
            if resp.status != warning_status:
                logging.warning(resp.status)
                logging.warning(resp.text)
        except aiohttp.ClientResponseError:
            logging.exception("Exception in response from Dynatrace API")
        except aiohttp.ClientConnectionError:
            logging.exception("Exception connecting to Dynatrace API")
        except aiohttp.ClientError:
            logging.exception("aiohttp client Exception")


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Process the problem information.

    Parameters
    ----------
    queue : asyncio.Queue
        Problem queue.
    args : Dict[str,Any])
        Args containing the host and API access token.
    """
    dt_api_host = args.get("dt_api_host")
    dt_api_token = args.get("dt_api_token")
    delay = int(args.get("delay", 60))
    try:
        while True:
            problems = await getproblems(dt_api_host, dt_api_token)
            for problem in problems.get("problems"):
                pr_comment = problem.get("recentComments").get("comments")
                commentcount = 0
                for comm in pr_comment:
                    contents = comm["content"]
                    if "EDA" in contents:
                        # ignore this problem
                        commentcount = commentcount + 1
                if commentcount > 0:
                    logging.info("This problem has already been sent to EDA server")
                else:
                    prob_id = problem.get("problemId")
                    await queue.put(problem)
                    # Once sent update comment to "Sent to EDA server"
                    await updatedtproblem(prob_id, dt_api_host, dt_api_token)
            await asyncio.sleep(delay)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logging.exception("Async request timed out or cancelled")
