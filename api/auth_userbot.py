from loader import app, database, bots, logger
from userbot import UserBot
from database import Bot
import asyncio
from telethon import TelegramClient, errors
from pydantic.dataclasses import dataclass
from typing import Optional
import os
@dataclass
class GetCodeData:
    phone: str
    api_id: str
    api_hash: str
    proxy: str
@dataclass
class AuthNewUserData:
    phone: str
    code: int
    api_id: str
    api_hash: str
    phone_code_hash: str
    proxy: str
    password: Optional[str] = None


@app.post('/get_code')
async def get_code(body: GetCodeData):
    proxy = body.proxy.split(":")
    proxy = {
        'proxy_type': 'socks5',
        'addr': f'{proxy[0]}',
        'port': int(proxy[1]),
        'username': f'{proxy[2]}',
        'password': f'{proxy[3]}'
    }
    try:
        try:
            os.remove(f"/app/sessions/{body.phone}.session")
            print(f"Файл {body.phone}.session успешно удален.")
        except FileNotFoundError:
            print(f"Файл {body.phone}.session не найден.")
        except PermissionError:
            print(f"Недостаточно прав для удаления файла {body.phone}.session.")
        except Exception as e:
            print(f"Не удалось удалить файл {body.phone}.session из-за следующей ошибки: {e}")
        new_client = TelegramClient(session=f"/app/sessions/{body.phone}", api_id=body.api_id, api_hash=body.api_hash, proxy=proxy)
        await new_client.connect()
        code_hash = await new_client.send_code_request(phone=body.phone)
        await new_client.disconnect()
        return {'status': "ok", 'phone_code_hash': code_hash.phone_code_hash}
    except Exception as e:
        return {'status': "error", 'description': e.args[0]}

@app.post("/auth_new_user")
async def auth_new_user(body: AuthNewUserData):
    proxy = body.proxy.split(":")
    proxy = {
        'proxy_type': 'socks5',
        'addr': f'{proxy[0]}',
        'port': int(proxy[1]),
        'username': f'{proxy[2]}',
        'password': f'{proxy[3]}'
    }
    try:
        new_client = TelegramClient(session=f"/app/sessions/{body.phone}", api_id=body.api_id, api_hash=body.api_hash, proxy=proxy)
        await new_client.connect()
        logger.info(f"Попытка авторизации {body.phone}, код: {body.code}, пароль: {body.password}")
        try:
            user = await new_client.sign_in(phone=body.phone, code=body.code, phone_code_hash=body.phone_code_hash)
            logger.info(f"Попытка авторизации {body.phone}, код: {body.code}")
        except errors.SessionPasswordNeededError:
            logger.info(f"Попытка авторизации {body.phone}, запрошен двухфакторный пароль")
            logger.info(f"Попытка авторизации {body.phone}, с двухфакторным паролем")
            user = await new_client.sign_in(password=body.password)
        await new_client.disconnect()
        logger.info(f"Успешная авторизация {body.phone}")

        database.add_record(Bot(phone=body.phone, api_id=body.api_id, api_hash=body.api_hash, proxy=body.proxy, name=user.first_name, user_id=user.id))
        # Запускаем нового бота
        bot_id = database.get_bot_id_by_phone(phone=body.phone)
        bot = UserBot(bot_id=bot_id, session=body.phone, api_id=body.api_id, api_hash=body.api_hash, proxy=body.proxy)
        bots[body.phone] = bot
        asyncio.create_task(bot.start())
        return {"status": "ok"}
    except Exception as e:
        logger.info(f"Ошибка авторизации {body.phone}, код: {body.code}, пароль: {body.password}, ОШИБКА: {e}")

        return {'status': "failed", 'error': e.args[0]}
