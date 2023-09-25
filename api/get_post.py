from loader import app, bots
from pydantic.dataclasses import dataclass
from typing import Optional, List
import re


@dataclass
class ChannelPost:
    url: str

@app.post("/get_post")
async def get_post(body: ChannelPost):
    for bot in bots.values():
        channel_id = await bot.check_url(url=body.url.split("/")[-2])
        if channel_id:
            result = await bot.get_post_content(url=body.url)
            return {"status":"ok",
                    "post":result}

    return {"status":"failed",
            "error": "channel not found"}