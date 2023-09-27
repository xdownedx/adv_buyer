from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
from loader import telegram_handler
import logging
import traceback

logger = logging.getLogger('uvicorn.error')
logger.addHandler(telegram_handler)
async def log_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
        logger.error("".join(tb_str))
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
