from loader import app, bots
from pydantic.dataclasses import dataclass
from typing import Optional, List
from .check_public_channel import is_channel_public
import re


@dataclass
class Channel:
    url: str

@app.post("/get_info_channel")
async def get_info_channel(body: Channel):
    try:
        if is_channel_public(body.url):
            bot = min(bots.values(), key=lambda x: x.request_count)
            channel_id = await bot.check_url(url=body.url.split("/")[-1])
            if channel_id:
                result = await bot.get_channel_info(channel_link=body.url)
                return {"status": "ok", "channel": result}
        else:
            for bot in bots.values():
                channel_id = await bot.check_url(url=body.url if not body.url.split("/")[-1].isdigit() else int(body.url.split("/")[-1]))
                if channel_id:
                    result = await bot.get_channel_info(channel_link=body.url)
                    return {"status":"ok", "channel":result}
    except Exception as e:
        return {"status":"failed", "error": e.args}