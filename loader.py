from fastapi import FastAPI
from database import Database, Bot  # Импортируем класс Database
from userbot import UserBot
from decouple import config

# Создаем экземпляр базы данных
database = Database(config("PG_URL"))
database.create_tables()  # Создаем таблицы, если они еще не существуют


# Инициализируем список ботов
bots = {}

# Получаем информацию о всех ботах из базы данных
session = database.Session()
all_bots_info = session.query(Bot).all()
session.close()

# Создаем экземпляр UserBot для каждого бота
for bot_info in all_bots_info:
    bot = UserBot(bot_info.phone, bot_info.api_id, bot_info.api_hash, bot_info.proxy, bot_info.bot_id)
    bots[bot_info.phone]=bot


app = FastAPI()
