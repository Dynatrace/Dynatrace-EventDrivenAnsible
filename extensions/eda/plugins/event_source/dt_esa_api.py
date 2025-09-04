"""Plugin pulls Dynatrace detected problems and sends it to the EDA server."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

# pylint: disable-next=import-error
import aiohttp

DOCUMENTATION = r"""
---
name: dt_esa_api.py
description:
  - This Event source plugin from Dynatrace captures all problems
    from your Dynatrace tenant and in conjunction with Ansible EDA
    rulebooks helps to enable auto-remediation in your environment.
options:
  dt_api_host:
    description:
      - The URL of the Dynatrace tenant
  dt_api_token:
    description:
      - The API token to connect to Dynatrace
  delay:
    description:
      - Delay between polling requests in seconds
    default: 60
  proxy:
    description:
      - Proxy URL through which to access host
    default: none
"""

EXAMPLES = r"""
- name: Listen for events on a webhook
  hosts: all
  sources:
    - dynatrace.event_driven_ansible.dt_esa_api:
        dt_api_host: "https://abc.live.dynatrace.com"
        dt_api_token: "<yourtoken>"
        delay: 60
        proxy: "http://my-proxy:3128"

  rules:
    - name: Problem payload Dynatrace for CPU issue
      condition: event.title is match("CPU saturation")
      action:
        run_job_template:
          name: "Remediate CPU saturation issue"
          organization: "Default"
    - name: Problem payload Dynatrace for App Failure rate increase issue
      condition: event.title is match("Failure rate increase")
      action:
        run_job_template:
          name: "Remediate Application issue"
          organization: "Default"
    - name: Update comments in Dynatrace
      condition:
        all:
          - event.status == "OPEN"
      action:
        run_playbook:
          name: dt-update-comments.yml
"""

logger = logging.getLogger(__name__)

# initialize logger configuration
def _initialize_logger_config() -> None:
    logging.basicConfig(
        format="[%(asctime)s] - %(pathname)s: %(message)s",
        level=logging.INFO,
        datefmt="%Y-%m-%d %I:%M:%S",
    )

async def getproblems(dt_host: str, dt_token: str, proxy: str) -> None:
    """Pull Dynatrace detected problems from Dynatrace Problems API.

    Parameters
    ----------
    dt_host : str
        Dynatrace host.
    dt_token : str
        Dynatrace access token.
    proxy: str
        Proxy through which to access host.

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
        async with session.get(url=url, proxy=proxy) as resp:
            try:
                return await resp.json()
            except aiohttp.ClientResponseError:
                logger.exception("Exception in response from Dynatrace API")
            except aiohttp.ClientConnectionError:
                logger.exception("Exception connecting to Dynatrace API")
            except aiohttp.ClientError:
                logger.exception("aiohttp client Exception")


async def updatedtproblem(prob_id: str, dtapihost: str, dtapitoken: str,
                          proxy: str) -> None:
    """Update problem comment once its sent to the EDA server.

    Parameters
    ----------
    prob_id : str
        Problem ID.
    dtapihost : str
        Host to query.
    dtapitoken: str
        Host API token.
    proxy: str
        Proxy through which to access host.

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
            resp = await session.post(url, json=commentbody, proxy=proxy)
            warning_status = 201
            if resp.status != warning_status:
                logger.warning(resp.status)
                logger.warning(resp.text)
        except aiohttp.ClientResponseError:
            logger.exception("Exception in response from Dynatrace API")
        except aiohttp.ClientConnectionError:
            logger.exception("Exception connecting to Dynatrace API")
        except aiohttp.ClientError:
            logger.exception("aiohttp client Exception")


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Process the problem information.

    Parameters
    ----------
    queue : asyncio.Queue
        Problem queue.
    args : Dict[str,Any])
        Args containing the host and API access token.

    """
    _initialize_logger_config()
    dt_api_host = args.get("dt_api_host")
    dt_api_token = args.get("dt_api_token")
    delay = int(args.get("delay", 60))
    proxy = args.get("proxy", "")
    try:
        while True:
            problems = await getproblems(dt_api_host, dt_api_token, proxy)
            for problem in problems.get("problems"):
                pr_comment = problem.get("recentComments").get("comments")
                commentcount = 0
                for comm in pr_comment:
                    contents = comm["content"]
                    if "EDA" in contents:
                        # ignore this problem
                        commentcount = commentcount + 1
                if commentcount > 0:
                    logger.info("This problem has already been sent to EDA server")
                else:
                    prob_id = problem.get("problemId")
                    await queue.put(problem)
                    # Once sent update comment to "Sent to EDA server"
                    await updatedtproblem(prob_id, dt_api_host, dt_api_token, proxy)
            await asyncio.sleep(delay)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        logger.exception("Async request timed out or cancelled")
