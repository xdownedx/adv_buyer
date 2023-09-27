from loader import app, database, bots, config
import uvicorn
import api
from database import Bot  # Импортируем модель Bot
import asyncio


async def run_fastapi():
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=config("PORT", cast=int), loop="asyncio")
    server = uvicorn.Server(config=uvicorn_config)
    await server.serve()

async def run_userbots():
    keys = bots.keys()
    await asyncio.gather(*(bots[key].start() for key in keys))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(run_fastapi(), run_userbots()))
