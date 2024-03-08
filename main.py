from typing import List

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.responses import RedirectResponse, JSONResponse

from app import api
from app.config import settings

app = FastAPI()


# register exception_handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": f"request params error: {exc.body}"
        },
    )


class Item(BaseModel):
    key: str
    list: List[str]


@app.get('/')
async def root():
    return RedirectResponse('/docs')


@app.get("/demo")
async def demo():
    """直接返回pydantic对象"""
    return Item(key='value', list=['a', 'b', 'c'])


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/info")
async def info():
    """
    获取配置信息
    :return:
    """
    return settings.model_dump()


app.include_router(api.router, prefix=settings.api_prefix)
