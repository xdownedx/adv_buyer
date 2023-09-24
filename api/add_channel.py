from loader import app, database, bots  # database is already imported
from userbot import UserBot
from database import Channel, ChannelBotRelation  # Import necessary models
from pydantic.dataclasses import dataclass
from typing import Optional
from database import Channel, ChannelBotRelation  # Import necessary models and session
from datetime import datetime
@dataclass
class ChannelURL:
    url: str

@app.post("/add_new_channel")
async def auth_new_channel(body: ChannelURL):
    # Initially checking if any bot already has access to the channel
    for bot_phone, bot in bots.items():
        channel_id = await bot.check_url(url=body.url)
        if channel_id:
            # If any bot can access the channel, no need to subscribe
            return {'status': "ok", 'channel_id': channel_id}

    # If no bot has access, find the bot with the minimum number of subscribed channels
    min_channels_bot = None
    min_channels_count = float('inf')

    for bot_phone, bot in bots.items():
        # Get the count of channels associated with the bot from the database
        channels_count = len(database.get_channels_by_bot_id(bot.bot_id))

        if channels_count < min_channels_count:
            min_channels_bot = bot
            min_channels_count = channels_count

    # Try subscribing the selected bot to the channel
    try:
        new_channel_entity = await min_channels_bot.sub_to_channel(url=body.url)
    except Exception as e:
        return {'status': "failed", 'error': f"Unable to access the channel: {str(e)}"}
    if new_channel_entity:
        # If subscription is successful, create a new channel entity and a new relation entity
        channel = Channel(
            telegram_id=new_channel_entity["id"],
            username=new_channel_entity.get("username"),
            name=new_channel_entity.get("title"),
            date_added=datetime.now()
        )
        database.add_record(channel)

        relation = ChannelBotRelation(bot_id=min_channels_bot.bot_id, channel_id=channel.channel_id)
        database.add_record(relation)

        return {'status': "ok", 'channel_id': new_channel_entity["id"]}
    else:
        return {'status': 'pending'}