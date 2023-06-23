"""Plugin pulls Dynatrace detected problems and sends it to the EDA server."""
from typing import Any, Dict
import aiohttp
import asyncio
import logging

async def getproblems(dt_host: str,dt_token: str):
    """Pull Dynatrace detected problems from Dynatrace Problems API."""
    timeout1 = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        headers=
        {"Authorization": f"Api-Token {dt_token}"},timeout=timeout1) as session:
        url = f"{dt_host}/api/v2/problems?fields=recentComments&from=now-10m&to=now"
        async with session.get(url) as resp:
            try:
                return await resp.json()
            except Exception as err:
                logging.exception("Error" + err.message)
                logging.warning(resp.status_code)
                logging.warning(resp.text)
                return {}

async def updatedtproblem(prob_id: str,dtapihost: str,dtapitoken: str):
    """Updates problem comment once its sent to the EDA server."""
    timeout1 = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        headers={"Authorization": f"Api-Token {dtapitoken}"},timeout=timeout1) as session:

        url = f"{dtapihost}/api/v2/problems/{prob_id}/comments"
        commentbody = {}
        commentbody["context"] = "Event Driven Ansible"
        commentbody["message"] = "Sent to EDA Server"
        r = await session.post(url,json=commentbody)
        if r.status != 201:
            logging.warning(r.status_code)
            logging.warning(r.text)

async def main(queue: asyncio.Queue, args: Dict[str,Any]):
    """Processes the problem information."""
    dt_api_host = args.get("dt_api_host")
    dt_api_token = args.get("dt_api_token")
    delay = int(args.get("delay", 40))
    while True:
        problems = await getproblems(dt_api_host,dt_api_token)
        for problem in problems.get("problems"):
            pr_comment = problem.get("recentComments").get("comments")
            commentcount = 0
            for comm in pr_comment:
                contents = comm["content"]
                if("EDA" in contents):
                    #ignore this problem
                    commentcount = commentcount + 1
            if commentcount > 0:
                logging.info("This problem has already been sent to EDA server")
            else:
                prob_id = problem.get("problemId")
                await queue.put(problem)
                # Once sent update comment to "Sent to EDA server"
                await updatedtproblem(prob_id,dt_api_host,dt_api_token)

        await asyncio.sleep(delay)
