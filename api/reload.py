from loader import app
import os
@app.get("/reload")
@app.post("/reload")
async def shutdown():
    os._exit(0)
    return {"status":"ok"}