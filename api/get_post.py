from loader import app, bots
from pydantic.dataclasses import dataclass
from typing import Optional, List
from .check_public_channel import is_channel_public
import re


@dataclass
class ChannelPost:
    url: str

@app.post("/get_post")
async def get_post(body: ChannelPost):
    try:
        if is_channel_public(body.url):
            bot = min(bots.values(), key=lambda x: x.request_count)
            channel_id = await bot.check_url(url=body.url.split("/")[-2])
            if channel_id:
                result = await bot.get_post_content(url=body.url)
                return {"status": "ok", "post": result}
        else:
            for bot in bots.values():
                channel_id = await bot.check_url(url=int(body.url.split("/")[-2]))
                if channel_id:
                    result = await bot.get_post_content(url=body.url)
                    return {"status":"ok", "post":result}
    except Exception as e:
        return {"status":"failed", "error": e.args}