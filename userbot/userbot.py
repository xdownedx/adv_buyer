import os
from database import Post, Media, Channel  # Импорт моделей вашей базы данных
from telethon import events
import json
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError, InviteRequestSentError
from telethon.events import NewMessage
from telethon.types import Message
import re
import base64

class UserBot:
    def __init__(self, session, api_id, api_hash, proxy, bot_id):
        proxy = proxy.split(":")
        proxy = {
            'proxy_type': 'socks5',
            'addr': f'{proxy[0]}',
            'port': int(proxy[1]),
            'username': f'{proxy[2]}',
            'password': f'{proxy[3]}'
        }
        self.client = TelegramClient(session=session, api_id=api_id, api_hash=api_hash, proxy=proxy)
        self.channels = []
        self.bot_id = bot_id

    async def start(self):
        await self.client.connect()
        self.initialize_handlers()
    async def check_url(self, url):
        try:
            entity = await self.client.get_entity(url)
            return entity.id
        except Exception as e:
            print(e)
            return None

    async def sub_to_channel(self, url):
        # Extracting the username, invite link or hash from the provided URL
        match = re.search(r"(?:https://t\.me/joinchat/|https://t\.me/\+|https://t\.me/|@)?([a-zA-Z0-9_\-]+)", url)
        if not match:
            raise ValueError("Invalid channel URL")

        channel_identifier = match.group(1)

        try:
            updates = await self.client(ImportChatInviteRequest(channel_identifier))
            channel_entity = await self.client.get_entity(updates.chats[0].id if updates.chats else updates.users[0].id)
        except UserAlreadyParticipantError:
            channel_entity = await self.client.get_entity(url)
            pass
        except InviteRequestSentError:
            return None
        except Exception as e:
            print(e)
            try:
                await self.client(JoinChannelRequest(channel=channel_identifier))
                channel_entity = await self.client.get_entity(channel_identifier)
            except Exception as e:
                raise ValueError(f"Unable to join channel with identifier {channel_identifier}. Error: {str(e)}")

        # Extracting relevant information from the channel entity
        channel_info = {
            "id": channel_entity.id,
            "username": getattr(channel_entity, "username", None),
            "title": getattr(channel_entity, "title", None),
            "description": getattr(channel_entity, "description", None),
        }

        return channel_info

    async def get_post_content(self, url):
        parts = url.split('/')
        channel = parts[-2]
        message_id = int(parts[-1].split('?')[0])
        message = await self.client.get_messages(channel, ids=message_id)

        def extract_links(text: str):
            url_pattern = re.compile(
                r'\b(?:http|https)://\S+\b|(?<=\()\S+(?=\))'
            )
            return url_pattern.findall(text)
        # Проверка наличия группы сообщений
        related_messages = []

        if message.grouped_id:
            # Извлекаем 10 предыдущих и 10 следующих сообщений
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
            "text": combined_text,
            "media": media_info,
            "entities": extract_links(combined_text)
        }
        return formatted_message

    async def fetch_channel_history(self, channel_id, limit=100, offset_id=0, extended = 1):
        from loader import database
        try:
            channel = await self.client.get_entity(channel_id)
            messages = await self.client.get_messages(channel, limit=limit, add_offset=limit*offset_id)
            formatted_messages = []
            grouped_messages = {}  # Словарь для хранения объединенных сообщений альбома

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
                            "views": message.views or 0,
                            "chat_id": message.chat_id,
                            "forwarded_from": message.forward.sender_id if message.forward else None,
                        }
                    grouped_messages[grouped_id]["texts"].append(message.text)
                    if message.media:
                        media_info = await self.extract_media_info(message.media, extended)
                        grouped_messages[grouped_id]["medias"].append(media_info)
                    continue
                formatted_message = await self.format_message(message, extended)
                formatted_messages.append(formatted_message)

            def extract_links(text: str):
                url_pattern = re.compile(
                    r'\b(?:http|https)://\S+\b|(?<=\()\S+(?=\))'
                )
                return url_pattern.findall(text)
            for grouped_id, grouped_message in grouped_messages.items():
                formatted_message = {
                        "id": int(grouped_id),
                        "date": grouped_message["date"],
                        "views": grouped_message["views"],
                        "link": f"t.me/{message.sender.username if message.sender.username else 'c/'+str(message.sender.id)}/{message.id}",
                        "forwarded_from": message.forward.from_id.channel_id if message.forward else None,
                        "is_deleted": 0,
                        "text": "\n".join(grouped_message["texts"]),
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

        # Получение или создание канала
        db_channel = database.get_record(Channel, telegram_id=message.chat_id)
        if not db_channel:
            db_channel = Channel(name=message.chat.title, telegram_id=message.chat_id)
            database.add_record(db_channel)
            db_channel = database.get_record(Channel, telegram_id=message.chat_id)

        # Форматирование сообщения
        formatted_message = {
                "id": message.id,
                "date": message.date.strftime('%d.%m.%Y %H:%M:%S'),
                "views": message.views or 0,
                "link": f"t.me/{message.sender.username if message.sender.username else 'c/'+str(message.sender.id)}/{message.id}",
                "channel_id": message.sender.id,
                "forwarded_from": message.forward.from_id.channel_id if message.forward else None,
                "is_deleted": 0,
                "text": message.text,
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
        channels = database.get_channels_by_bot_id(self.bot_id)
        self.channels = [channel.telegram_id for channel in channels]

        @self.client.on(events.ChatAction())
        async def handler(event):
            # Получаем ID канала из события
            channel_id = event.channel_id
            # Получаем информацию о канале
            try:
                channel = await self.client.get_entity(channel_id)
                print(f"Заявка принята! Вы теперь участник {channel.title}!")
            except Exception as e:
                print(f"Не удалось получить информацию о канале с ID {channel_id}. Ошибка: {e}")

        #@self.client.on(events.Album())
        async def new_album(event):
            # Обработка альбомов
            await save_post(event)

        #@self.client.on(events.NewMessage())
        async def new_message(event):
            # Проверка, является ли сообщение частью альбома
            if event.message.grouped_id:
                return
            # Обработка обычных сообщений
            await save_post(event)

        async def save_post(event):
            try:
                messages = event.messages if hasattr(event, 'messages') else [event.message]
                for message in messages:
                    # Получение или создание канала
                    channel = database.get_record(Channel, telegram_id=message.chat_id)
                    if not channel:
                        channel = Channel(name=message.chat.title, telegram_id=message.chat_id)
                        database.add_record(channel)
                        channel = database.get_record(Channel, telegram_id=message.chat_id)  # Получение созданного канала

                    # Создание поста
                    post = Post(
                        channel_id=channel.channel_id,
                        content={"text": message.text},
                        views_count=message.views or 0,
                        link=f"t.me/c/{message.chat_id*(-1)-1000000000000}/{message.id}",
                        forwarded_from=message.forward.sender_id if message.forward else None,
                        date_time=message.date
                    )
                    database.add_record(post)
                    post = database.get_record(Post, channel_id=channel.channel_id,
                                         date_time=message.date)  # Получение созданного поста

                    # Сохранение медиафайлов
                    if message.media:
                        media_list = message.media if isinstance(message.media, list) else [message.media]
                        for media in media_list:
                            media_info = await extract_media_info(media)
                            media_record = Media(
                                post_id=post.post_id,
                                media_type=media_info["media_type"],
                                caption=media_info["caption"],
                                content=media_info["content"]
                            )
                            database.add_record(media_record)
            except Exception as e:
                print(f"Error saving post: {e}")

        async def extract_media_info(media):
            # Extract media type, caption, and base64 content from media object
            media_type = "media" + type(media).__name__[7:]
            caption = media.caption if hasattr(media, 'caption') else ""

            # Downloading the media and converting to base64
            file_path = await self.client.download_media(media)
            with open(file_path, "rb") as file:
                base64_content = base64.b64encode(file.read()).decode('utf-8')
            os.remove(file_path)

            return {"media_type": media_type, "caption": caption, "content": base64_content}

        @self.client.on(event=events.Raw)
        async def get_newwww(event):
            print(event)


