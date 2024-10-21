from typing import List

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse, RedirectResponse

from app import api
from app.config import settings

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="创意生成")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# register exception_handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": f"request params error: {exc.body}"},
    )


class Item(BaseModel):
    key: str
    list: List[str]


@app.get("/")
async def root():
    return RedirectResponse("/docs")


app.include_router(api.router, prefix=settings.api_prefix)
