from loader import app, bots, database
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
        if "https://" not in body.url:
            body.url = "https://"+body.url
        for bot in bots.values():
            try:
                channel_id = await bot.check_url(url=int(body.url.split("/")[-2]))
                if channel_id:
                    try:
                        result = await bot.get_post_content(url=body.url)
                        return {"status":"ok", "post":result}
                    except Exception as e:
                        return {"status": "failed", "error": e.args[0]}
            except:
                pass
    except Exception as e:
        return {"status":"failed", "error": e.args[0]}
    return {'status':"failed", 'error': "channel_not_found"}