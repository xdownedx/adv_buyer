from loader import app, database, bots  # database is already imported
from pydantic.dataclasses import dataclass
from typing import Optional
from .check_public_channel import is_channel_public
from database import Channel
from datetime import datetime
@dataclass
class ChannelURL:
    url: str
@app.post("/remove_channel")
async def add_new_channel(body: ChannelURL):
    try:

        if body.url == 'all':
            database.delete_all_channels()
            for bot in bots.values():
                await bot.unsub_all()
            return {'status':"ok"}
        if "https://" not in body.url:
            body.url = "https://"+body.url
        if is_channel_public(body.url):
            for bot in bots.values():
                try:
                    channel_url = int(body.url) if body.url.isdigit() else body.url
                    channel_id = await bot.check_url(url=channel_url)
                    if channel_id:
                        # If any bot can access the channel, no need to subscribe
                        await bot.unsub_to_channel(channel_id=channel_id)
                        try:
                            database.delete_record(Channel, telegram_id=channel_id)
                        except:
                            pass
                        return {'status': "ok", 'channel': channel_id}
                except Exception as e:
                    return {'status': 'fail', "error": e.args[0]}
        else:
            for bot in bots.values():
                try:
                    channel_url = int(body.url) if body.url.isdigit() else body.url
                    channel_id = await bot.check_url(url=channel_url)
                    if channel_id:
                        # If any bot can access the channel, no need to subscribe
                        await bot.unsub_to_channel(channel_id=channel_id)
                        try:
                            database.delete_record(Channel, telegram_id=channel_id)
                        except:
                            pass
                        return {'status': "ok", 'channel': channel_id}
                except Exception as e:
                    return {'status': 'fail', "error":e.args[0]}
            return {'status': 'fail', "error": "channel not found"}
    except Exception as e:
        return {"status":"failed", "error": e.args[0]}