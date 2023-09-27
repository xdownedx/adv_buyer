from loader import app, bots

@app.post("/health")
async def get_info_channel():
    result = []
    for bot in bots.values():
        result.append({
        "phone":bot.phone,
        "status": await bot.get_userbot_status(),
        "request_count": bot.request_count,
        "proxy": bot.proxy})
    return {"result": result}