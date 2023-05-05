import asyncio
import aiohttp
import logging
import json

from typing import Any, Dict

async def getProblems(dt_host,dt_token):
    timeout1 = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(headers={"Authorization": f"Api-Token {dt_token}"},timeout=timeout1) as session:
        #dt_tag_encode = urllib.parse.urlencode(dt_tag)
        url = f"{dt_host}/api/v2/problems?fields=recentComments&from=now-10m&to=now"
        async with session.get(url) as resp:

            try:
                return await resp.json()
            except Exception as err:
                logging.exception(err)
                logging.warning(resp.status_code)
                logging.warning(resp.text)
                return {}  

async def updateDTProblem(prob_id,dtAPIHost,dtAPIToken):
    timeout1 = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(headers={"Authorization": f"Api-Token {dtAPIToken}"},timeout=timeout1) as session:

        url = f"{dtAPIHost}/api/v2/problems/{prob_id}/comments"
        commentbody = {}
        commentbody["context"] = "Event Driven Ansible"
        commentbody["message"] = "Sent to EDA Server"
    
        #print(commentbody)
        r = await session.post(url,json=commentbody)
        if r.status != 201:
            logging.warn(r.status_code)
            logging.warn(r.text)

async def main(queue: asyncio.Queue, args: Dict[str, Any]):

    dt_api_host = args.get("dt_api_host")
    dt_api_token = args.get("dt_api_token")
    #dt_entity_tag = args.get("dt_entity_tags")

    delay = int(args.get("delay", 40))

    while True:
        #try:
        problems = await getProblems(dt_api_host,dt_api_token)
        for problem in problems.get("problems"):
            #async with session.get(problem) as resp:
            pr_comment = problem.get("recentComments").get("comments")
            commentcount = 0
            for comm in pr_comment:
                contents = comm["content"]
                if("EDA" in contents):
                    #ignore this problem
                    commentcount = commentcount + 1
                
            if(commentcount > 0):
                print("This problem has already been sent to EDA server")
                logging.info("This problem has already been sent to EDA server")
            else:
                prob_id = problem.get("problemId")

                await queue.put(problem)

                # Once sent update comment to "Sent to EDA server"
                await updateDTProblem(prob_id,dt_api_host,dt_api_token)
            
        await asyncio.sleep(delay)
