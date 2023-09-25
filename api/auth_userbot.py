from loader import app, database
from userbot import UserBot
from database import Bot
import asyncio
from telethon import TelegramClient
from pydantic.dataclasses import dataclass
from typing import Optional

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
        new_client = TelegramClient(session=body.phone, api_id=body.api_id, api_hash=body.api_hash, proxy=proxy)
        await new_client.connect()
        code_hash = await new_client.send_code_request(phone=body.phone)
        await new_client.disconnect()
        return {'status': "ok", 'phone_code_hash': code_hash.phone_code_hash}
    except Exception as e:
        return {'status': "error", 'description': e.args}

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
        new_client = TelegramClient(session=body.phone, api_id=body.api_id, api_hash=body.api_hash, proxy=proxy)
        await new_client.connect()
        user = await new_client.sign_in(phone=body.phone, code=body.code, password=body.password, phone_code_hash=body.phone_code_hash)

        database.add_record(Bot(phone=body.phone, api_id=body.api_id, api_hash=body.api_hash, proxy=body.proxy, name=user.first_name, user_id=user.id))
        # Запускаем нового бота
        bot = UserBot(bot_id=user.id, session=body.phone, api_id=body.api_id, api_hash=body.api_hash, proxy=body.proxy)
        asyncio.create_task(bot.client.start())
        asyncio.create_task(bot.client.run_until_disconnected())
        return {"status": "ok"}
    except Exception as e:
        return {'status': "failed", 'error': e.args}
