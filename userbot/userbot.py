from telethon.utils import get_display_name
import re
import os
from database import Post, Media, Channel, ChannelBotRelation # Импорт моделей вашей базы данных
from telethon import events
from telethon.tl.types import MessageEntityMention, MessageEntityUrl

import json
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest, GetFullChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError, InviteRequestSentError
from telethon.events import NewMessage
from telethon.types import Message
from datetime import datetime
import re
import base64
from .helpers import markdown_to_text
class UserBot:
    def __init__(self, session, api_id, api_hash, proxy, bot_id):
        proxy = proxy.split(":")
        self.proxy = {
            'proxy_type': 'socks5',
            'addr': f'{proxy[0]}',
            'port': int(proxy[1]),
            'username': f'{proxy[2]}',
            'password': f'{proxy[3]}'
        }
        self.phone = session
        self.client = TelegramClient(session=f"/app/sessions/{session}", api_id=api_id, api_hash=api_hash, proxy=self.proxy)
        self.channels = []
        self.bot_id = bot_id
        self.status = "ok"
        self.request_count = 0
    async def start(self):
        try:
            from loader import logger
            await self.client.connect()
            await self.client.start()
            self.initialize_handlers()
            logger.info(f"{self.phone} успешно запущена сессия")
            from database import Bot
            from loader import database
            """Increment the request count and manage the session directly."""
            # Create a new session
            session = database.Session()
            bot_record = session.query(Bot).filter(Bot.phone == self.phone).first()
            if bot_record:
                bot_record.request_count += 1
                self.request_count = bot_record.request_count

        except Exception as e:
            logger.error(f"{self.phone} не смог запустить сессию! Ошибка: {e}")


    async def check_url(self, url):
        try:
            await self.increment_request_count()
            entity = await self.client.get_entity(url)
            return entity.id
        except ValueError as e:
            raise ValueError(f"Not found channel by '{url}'")

    async def increment_request_count(self):
        from database import Bot
        from loader import database
        """Increment the request count and manage the session directly."""
        # Create a new session
        session = database.Session()
        bot_record = session.query(Bot).filter(Bot.phone == self.phone).first()
        if bot_record:
            bot_record.request_count += 1
            self.request_count = bot_record.request_count
            session.commit()
        session.close()

    async def get_userbot_status(self):
        try:
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                return "ok", me.username
            else:
                return "fail", None
        except:
            return "fail", None

    async def sub_to_channel(self, url):
        # Extracting the username, invite link or hash from the provided URL
        match = re.search(r"(?:https://t\.me/joinchat/|https://t\.me/\+|https://t\.me/|@)?([a-zA-Z0-9_\-]+)", url)
        if not match:
            raise ValueError("Invalid channel URL")

        channel_identifier = match.group(1)

        try:
            await self.increment_request_count()
            updates = await self.client(ImportChatInviteRequest(channel_identifier))
            channel_entity = await self.client.get_entity(url)
        except UserAlreadyParticipantError as err:
            print(err)
            await self.increment_request_count()
            channel_entity = await self.client.get_entity(url)
            pass
        except InviteRequestSentError:
            return None
        except Exception as e:
            print(e)
            try:
                await self.increment_request_count()
                await self.client(JoinChannelRequest(channel=channel_identifier))
                channel_entity = await self.client.get_entity(channel_identifier)
            except Exception as e:
                raise ValueError(f"Unable to join channel with identifier {channel_identifier}. Error: {str(e)}")

        # Extracting relevant information from the channel entity
        channel_info = {
            "id": channel_entity.id,
            "username": channel_entity.username,
            "title": channel_entity.title,
        }

        return channel_info

    async def unsub_all(self):
        channels = await self.client.get_dialogs()
        for channel in channels:
            try:
                await self.client(LeaveChannelRequest(channel=channel.entity))
            except Exception as e:
                print(e)
                pass
    async def unsub_to_channel(self, channel_id):
        entity = await self.client.get_entity(channel_id)
        try:
            await self.increment_request_count()
            updates = await self.client(LeaveChannelRequest(entity))

        except Exception as e:
            raise ValueError(f"Unable to leave from channel with identifier {channel_id}. Error: {str(e)}")


    async def get_post_content(self, url):
        parts = url.split('/')
        channel = int(parts[-2]) if parts[-2].isdigit() else parts[-2]
        message_id = int(parts[-1].split('?')[0])
        message = await self.client.get_messages(channel, ids=message_id)
        if not message:
            raise ValueError("Post not found")
        def extract_links(text: str):
            url_pattern = re.compile(
                r'\b(?:http|https)://\S+\b|(?<=\()\S+(?=\))'
            )
            return url_pattern.findall(text)
        # Проверка наличия группы сообщений
        related_messages = []

        if message.grouped_id:
            # Извлекаем 10 предыдущих и 10 следующих сообщений
            await self.increment_request_count()
            surrounding_messages = await self.client.get_messages(channel, min_id=message_id - 10,
                                                                  max_id=message_id + 10)

            # Фильтруем сообщения с таким же grouped_id
            related_messages.extend([msg for msg in surrounding_messages if msg.grouped_id == message.grouped_id])

        if len(related_messages) == 0:
            related_messages.append(message)
        # Объединяем тексты сообщений
        combined_text = "\\n".join(msg.text for msg in related_messages)

        # Получение информации о медиа
        media_info = [await self.extract_media_info(msg.media, extended=1) for msg in related_messages if msg.media]

        # Форматирование сообщения для вывода
        formatted_message = {
            "id": message.id,
            "date": message.date.strftime('%d.%m.%Y %H:%M:%S'),
            "views": message.views or 0,
            "link": f"t.me/{message.sender.username if message.sender.username else 'c/'+str(message.sender.id)}/{message.id}",
            "channel_id": message.sender.id,
            "forwarded_from": message.forward.from_id.channel_id if message.forward else None,
            "is_deleted": 0 if combined_text else 1,
            "text": markdown_to_text(combined_text),
            "media": media_info,
            "entities": extract_links(combined_text)
        }
        return formatted_message

    async def get_channel_info(self, channel_link):
        try:
            # Fetching the channel entity
            await self.increment_request_count()
            await self.increment_request_count()

            entity = await self.client.get_entity(channel_link)
            full_channel = await self.client(GetFullChannelRequest(channel=entity))
            # Constructing the channel info
            channel_info = {
                "id": entity.id,
                "title": entity.title,
                "about": full_channel.full_chat.about,
                "link": f"t.me/{entity.username if entity.username else entity.id}",
                "subscribers_count": full_channel.full_chat.participants_count,
                "created_date": entity.date.strftime('%d.%m.%Y %H:%M:%S'),
                "peer_type": "channel",
                "is_scam": entity.scam,
                "username": f"@{entity.username}" if entity.username else None,
                "active_usernames": [f"@{username for username in entity.usernames}"] if entity.usernames else [entity.username if entity.username else None],
            }
            return channel_info
        except Exception as e:
            print(f"Error fetching channel info: {e}")
            return None

    async def fetch_channel_history(self, channel_id, limit=100, offset_id=0, extended = 1):
        from loader import database
        try:
            await self.increment_request_count()
            await self.increment_request_count()
            channel = await self.client.get_entity(channel_id)
            messages = await self.client.get_messages(channel, limit=limit, add_offset=limit*offset_id)
            formatted_messages = []
            grouped_messages = {}  # Словарь для хранения объединенных сообщений альбома

            def extract_links(text: str):
                url_pattern = re.compile(
                    r'\b(?:http|https)://\S+\b|(?<=\()\S+(?=\))'
                )
                return url_pattern.findall(text)

            for message in messages:
                if message.id <= offset_id:
                    continue  # Skip messages with ID less than or equal to offset_id

                # Если сообщение является частью альбома, объединяем его с другими сообщениями альбома
                if message.grouped_id:
                    grouped_id = str(message.grouped_id)
                    if grouped_id not in grouped_messages:
                        grouped_messages[grouped_id] = {
                            "texts": [],
                            "medias": [],
                            "id": message.id,
                            "date": message.date.strftime('%d.%m.%Y %H:%M:%S'),
                            "link": f"t.me/{message.sender.username if message.sender.username else 'c/'+str(message.sender.id)}/{message.id}",
                            "views": message.views or 0,
                            "chat_id": message.chat_id,
                            "forwarded_from": message.forward.sender_id if message.forward else None,
                        }
                    grouped_messages[grouped_id]["texts"].append(markdown_to_text(message.text))
                    if message.media:
                        media_info = await self.extract_media_info(message.media, extended)
                        grouped_messages[grouped_id]["medias"].append(media_info)
                    continue
                formatted_message = await self.format_message(message, extended)
                formatted_messages.append(formatted_message)

            for grouped_id, grouped_message in grouped_messages.items():
                formatted_message = {
                        "id": grouped_message['id'],
                        "date": grouped_message["date"],
                        "views": grouped_message["views"],
                        "link": grouped_message['link'],
                        "forwarded_from": grouped_message['forwarded_from'],
                        "is_deleted": 0,
                        "text": markdown_to_text("\n".join(grouped_message["texts"])),
                        "media": grouped_message["medias"],
                        "entities": extract_links("\n".join(grouped_message["texts"]))
                }
                formatted_messages.append(formatted_message)
            return formatted_messages
        except Exception as e:
            print(f"Error fetching channel history: {e}")
            return []

    async def format_message(self, message, extended):
        from loader import database

        def extract_links(text: str):
            url_pattern = re.compile(
                r'\b(?:http|https)://\S+\b|(?<=\()\S+(?=\))'
            )
            return url_pattern.findall(text)

        # Форматирование сообщения
        formatted_message = {
                "id": message.id,
                "date": message.date.strftime('%d.%m.%Y %H:%M:%S'),
                "views": message.views or 0,
                "link": f"t.me/{message.sender.username if message.sender.username else 'c/'+str(message.sender.id)}/{message.id}",
                "channel_id": message.sender.id,
                "forwarded_from": message.forward.from_id.channel_id if message.forward else None,
                "is_deleted": 0,
                "text": markdown_to_text(message.text),
                "markdown_text": message.text,
                "media": await self.extract_media_info(message.media, extended=extended) if message.media else None,
                "entities":extract_links(message.text)
        }
        return formatted_message

    async def extract_media_info(self, media, extended):
        # Extract media type, caption, and base64 content from media object
        media_type = "media" + type(media).__name__[7:]
        caption = media.caption if hasattr(media, 'caption') else ""

        # Downloading the media and converting to base64
        if extended == 1:
            await self.increment_request_count()
            file_path = await self.client.download_media(media)
            try:
                with open(file_path, "rb") as file:
                    base64_content = base64.b64encode(file.read()).decode('utf-8')
                os.remove(file_path)
                return {"media_type": media_type, "caption": caption, "content": base64_content}

            except:
                return {"media_type": media_type, "caption": caption}
        else:
            return {"media_type": media_type, "caption": caption}
    def initialize_handlers(self):
        from loader import database
        from loader import logger

        channels = database.get_channels_by_bot_id(self.bot_id)
        self.channels = [channel.telegram_id for channel in channels]

        def extract_links(text: str):
            url_pattern = re.compile(
                r'\b(?:http|https)://\S+\b|(?<=\()\S+(?=\))'
            )
            return url_pattern.findall(text)

        #@self.client.on(events.Album)
        async def album_handler(event):
            channel_id = event.messages[0].peer_id.channel_id
            if channel_id == 1698919256:
                return

            if not database.is_channel_in_db(channel_id):
                channel = await self.client.get_entity(channel_id)
                new_channel = Channel(
                    telegram_id=channel_id,
                    username=channel.username if hasattr(channel, 'username') else None,
                    name=channel.title,
                    date_added=datetime.now()
                )
                database.add_record(new_channel)
                channel_bot_relation = ChannelBotRelation(
                    bot_id=self.bot_id,
                    channel_id=database.get_channel_id_by_tg_id(channel_id)
                )
                database.add_record(channel_bot_relation)
                logger.info(f"{self.phone}: Канал {channel.title} добавлен в базу данных.")

            message_text = event.messages[0].text
            if message_text:
                try:
                    urls = [entity for entity in event.messages[0].entities if
                            isinstance(entity, (MessageEntityMention, MessageEntityUrl))]
                except:
                    return
                if len(urls) >= 2:
                    channel_username = await self.client.get_entity('https://t.me/+uj_WrikveVo3MmEy')
                    source_channel = await self.client.get_entity(channel_id)
                    new_message_text = f"From {source_channel.title}:\n\n{message_text}"

                    if event.messages[0].sender.noforwards:
                        media_files = []
                        try:
                            # Download all media files from the album
                            for message in event.messages:
                                if hasattr(message, 'media'):
                                    media_file = await self.client.download_media(message)
                                    media_files.append(media_file)

                            # Send message with media
                            await self.client.send_message(channel_username, new_message_text, file=media_files)
                            logger.info(
                                f"Copied album with multiple links from {get_display_name(event.messages[0].sender_id)} to {channel_username}")
                        except Exception as e:
                            logger.error(f"Failed to send copied album: {e}")
                        finally:
                            # Delete the downloaded media files
                            for media_file in media_files:
                                if os.path.exists(media_file):
                                    os.remove(media_file)
                    else:
                        try:
                            await event.forward_to(channel_username)
                            logger.info(
                                f"Album with multiple links from {get_display_name(event.messages[0].sender_id)} forwarded to {channel_username}")
                        except Exception as e:
                            logger.error(f"Failed to forward album: {e}")

        #@self.client.on(events.NewMessage())
        async def new_message_handler(event):
            channel_id = event.message.peer_id.channel_id
            if channel_id == 1698919256 or event.message.grouped_id != None:
                return

            if not database.is_channel_in_db(channel_id):
                channel = await self.client.get_entity(channel_id)
                new_channel = Channel(
                    telegram_id=channel_id,
                    username=channel.username if hasattr(channel, 'username') else None,
                    name=channel.title,
                    date_added=datetime.now()
                )
                database.add_record(new_channel)
                channel_bot_relation = ChannelBotRelation(
                    bot_id=self.bot_id,
                    channel_id=database.get_channel_id_by_tg_id(channel_id)
                )
                database.add_record(channel_bot_relation)
                logger.info(f"{self.phone}: Канал {channel.title} добавлен в базу данных.")



