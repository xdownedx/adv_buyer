from loader import app, database, bots  # database is already imported
from userbot import UserBot
from database import Channel, ChannelBotRelation  # Import necessary models
from pydantic.dataclasses import dataclass
from typing import Optional
from loader import logger
from .check_public_channel import is_channel_public
from database import Channel, ChannelBotRelation  # Import necessary models and session
from datetime import datetime
@dataclass
class ChannelURL:
    url: str

@app.post("/add_new_channel")
async def add_new_channel(body: ChannelURL):
    try:
        if "https://" not in body.url:
            body.url = "https://"+body.url
        for bot in bots.values():
            try:
                channel_id = await bot.check_url(url=body.url)
                if channel_id:
                    if database.is_channel_in_db(channel_id=channel_id):
                        channel = await bot.get_channel_info(channel_link=channel_id)
                        return {'status': "ok", 'channel': {'id': channel['id'], 'title': channel['title']}}
            except:
                pass

        filtered_bots = {bot_id: bot for bot_id, bot in bots.items()
                         if bot.floodwait is None or bot.floodwait < datetime.now()}

        # Находим бота с наименьшим количеством каналов среди отфильтрованных ботов
        min_channels_bot = min(filtered_bots.values(), key=lambda x: len(database.get_channels_by_bot_id(x.bot_id)))
        try:
            new_channel_entity = await min_channels_bot.sub_to_channel(url=body.url)
        except Exception as e:
            if "FLOOD" in str(e):
                return {'status': "failed", 'error': f"{str(e)}"}
            else:
                return {'status': "failed", 'error': f"Unable to access the channel: {str(e)}"}

        if new_channel_entity:
            channel = Channel(
                telegram_id=new_channel_entity["id"],
                username=new_channel_entity.get("username"),
                name=new_channel_entity.get("title"),
                date_added=datetime.now()
            )
            database.add_record(channel)  # Добавление канала в БД

            # Создание и добавление связи между ботом и каналом в БД
            channel_bot_relation = ChannelBotRelation(
                bot_id=min_channels_bot.bot_id,
                channel_id=database.get_channel_id_by_tg_id(new_channel_entity["id"])
            )
            database.add_record(channel_bot_relation)
            min_channels_bot.channels.append(new_channel_entity['id'])
            logger.info(f"{min_channels_bot.phone}: Канал {new_channel_entity['title']} добавлен в базу данных.")
            return {'status': "ok", 'channel': {'id': new_channel_entity['id'], 'title': new_channel_entity['title']}}

        else:
            return {'status': 'pending'}

    except Exception as e:
        return {"status": "failed", "error": str(e)}