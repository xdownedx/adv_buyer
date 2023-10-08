from loader import app, database, bots  # database is already imported
from userbot import UserBot
from database import Channel, ChannelBotRelation  # Import necessary models
from pydantic.dataclasses import dataclass
from typing import Optional
from .check_public_channel import is_channel_public
from database import Channel, ChannelBotRelation  # Import necessary models and session
from datetime import datetime
@dataclass
class ChannelURL:
    url: str
@app.post("/remove_channel")
async def add_new_channel(body: ChannelURL):
    # Initially checking if any bot already has access to the channel
    try:
        if is_channel_public(body.url):
            bot = min(bots.values(), key=lambda x: x.request_count)
            channel_id = await bot.check_url(url=body.url.split("/")[-1])
            if channel_id:
                await bot.get_channel_info(channel_link=channel_id)
                return {"status": "fail", "error": "channel is public"}
        else:
            for bot in bots.values():
                try:
                    channel_id = await bot.check_url(url=body.url)
                    if channel_id:
                        # If any bot can access the channel, no need to subscribe
                        channel = await bot.unsub_to_channel(channel_link=channel_id)
                        database.delete_record(Channel, telegram_id=channel_id)
                        return {'status': "ok", 'channel': channel}
                except Exception as e:
                    return {'status': 'fail', "error":e}
            return {'status': 'fail', "error": "channel not found"}
    except Exception as e:
        return {"status":"failed", "error": e.args[0]}