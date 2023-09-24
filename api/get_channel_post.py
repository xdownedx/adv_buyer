from loader import app, bots
from pydantic.dataclasses import dataclass
from typing import Optional, List
import re


@dataclass
class ChannelPost:
    url: str
    limit: Optional[int] = 20
    offset: Optional[int] = 0
    extended: Optional[int] = 0


def extract_links(text: str) -> List[str]:
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    return url_pattern.findall(text)


@app.post("/get_channel_posts")
async def get_channel_posts(body: ChannelPost):
    for bot in bots.values():
        channel_id = await bot.check_url(url=body.url)
        if channel_id:
            result = await bot.fetch_channel_history(channel_id=channel_id, limit=body.limit, offset_id=body.offset, extended=body.extended)
            return {"status":"ok",
                    "items":result}

    return {"status":"error",
            "response": "channel not found"}