import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Sequence

from fastapi import APIRouter, Depends, WebSocket
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field
from redis.asyncio import Redis
from snowflake import Snowflake, SnowflakeGenerator
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.dependency import get_db, get_rate_limiter, get_redis_cache
from app.discord_api import handle_imagine_prompt, imagine
from app.models import PatternPreset
from app.schemas import ImagineParameter, ImaginePrompt
from app.utils import RateLimiter

# from starlette.websockets import WebSocket


router = APIRouter()


def unique_id():
    """生成唯一的 10 位数字，作为任务 ID"""
    return (
        int(hashlib.sha256(str(time.time()).encode("utf-8")).hexdigest(), 16) % 10**10
    )


async def imagine_old1(prompt: ImaginePrompt):
    # 处理提示词
    handled_prompt = await handle_imagine_prompt(prompt.prompt)
    # 将任务添加到Celery队列

    # discord_api.generate()
    # r = await get_redis_connection()
    # await r.lpush('midjourney:tasks', prompt.model_dump_json())
    # TODO 异步处理任任务, 而不是直接将请求发送到midjourney bot

    return {
        "message": "任务已添加到队列",
        "data": {
            "prompt": handled_prompt,
            # "style": prompt.style,
            "task_id": "",
        },
    }


# @router.post("/imagine")
# async def imagine_api(prompt: ImaginePrompt):
#     await imagine_old1(prompt)


# @router.post("/generate_message")
# async def generate_message(prompt: str):
#     """
#     轮询接口, 用于获取生成的消息
#     :param prompt:
#     :return:
#     """
#     ...


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/api/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


# @router.get("/db")
# async def db_get(
#     # db: Annotated[Session, Depends(get_db)]
#     db: DBSession,
# ):
#     texture = db.get(PatternPreset, 1)
#
#     return texture


# @router.get("/html")
# async def get():
#     return HTMLResponse(html)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, trigger_id: str):
        await websocket.accept()
        if trigger_id not in self.active_connections:
            self.active_connections[trigger_id] = []
        self.active_connections[trigger_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, trigger_id: str):
        self.active_connections[trigger_id].remove(websocket)
        if not self.active_connections[trigger_id]:
            del self.active_connections[trigger_id]
        # self.active_connections.remove(websocket)

    async def send_message(self, message: dict, trigger_id: str):
        if trigger_id in self.active_connections:
            for connection in self.active_connections[trigger_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{trigger_id}")
async def websocket_endpoint(websocket: WebSocket, trigger_id: str):
    """
    Deprecated
    实时推送图像
    :param websocket:
    :param trigger_id:
    :return:
    """
    await manager.connect(websocket, trigger_id)
    try:
        while True:
            # 从Discord bot 接收图像消息
            data = await websocket.receive_json()
            # 将图像发送给已连接的客户端
            await manager.send_message(data, trigger_id)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, trigger_id)
    # await websocket.accept()
    # while True:
    #     data = await websocket.receive_text()
    #     await websocket.send_text(f"Message text was: {data}")


@router.websocket("/ws_imagine")
async def warning_event_server(
    websocket: WebSocket,
    # db: Session = Depends(get_db)
):
    """
    实时推送生成状态
    :param websocket:
    :param db:
    :return:
    """
    await websocket.accept()
    while True:
        # 查询数据库
        # 查询条件 最近5
        # db.query(models.WarningEventMessage).filter()
        data: dict = await websocket.receive_json()
        if data[""]:
            pass
        # log.info(f"接收信息成功:{data}")
        await websocket.send_json({"message": "接收信息成功", "data": data})
        await websocket.send_text(f"Message text was: {type(data)}")
        await asyncio.sleep(settings.warning_interval)


# @router.post("/create_celery_task")
# async def trigger_task(name: str):
#     result = background_task.delay(name)
#     return {"message": "Task triggerred!", "task_id": result.id}


# @router.get("/get_celery_task")
# async def get_celery_task(task_id: str):
#     """
#     通过任务ID轮询处理状态
#     :param task_id:
#     :return:
#     """
#     result = background_task.AsyncResult(task_id)
#     if result.ready():
#         return {"result": result.get()}
#     else:
#         return {"status": "pending"}


class CreativeGenerateParams(BaseModel):
    config: dict | None = Field(None, description="配置")
    request_id: str | int | None = Field(
        None, description="任务请求ID, 用于跟踪请求, 不传则自动创建"
    )
    prompt: str = Field(..., description="提示词")
    parameter: ImagineParameter | None = Field(None, description="参数")
    instructions: str | None = Field(
        None, description="翻译指令, 控制如何翻译输入的prompt"
    )
    texture_id: str | int | None = Field(None, description="纹理ID")
    wait_result: bool | None = Field(False, description="是否等待结果")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                # "config": {"batch_size": 4},
                "parameter": {"aspect": "4:3", "tile": False},
                "prompt": "条形,平滑",
                "texture_id": 3,
                "wait_result": True,
            }
        }
    )


@router.post("/creative_generate", summary="【必需】创意生成接口")
async def generate_creative(
    params: CreativeGenerateParams,
    db: Session = Depends(get_db),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    cache: Redis = Depends(get_redis_cache),
):
    """
    创意生成 一共返回四张,返回单张图片分辨率为2000*2000, 无缝模式(tiled, seamless)则为1000*1000. 主要有两种方式, config 参数为可选, 不传
    方式一: 不走数据库, 直接传入prompt, 可选自定义指令, 用于控制如何翻译和扩展prompt
    方式二: 通过`GET /api/creative_generate/preset` 获取预设列表, 然后通过预设id texture_id 比如(texture_id=3)来获取预设的instructions, parameter, 依然需要传入prompt

    关于获取返回结果:
    方式一: 不等待结果设置wait_result=False(默认值, 可不传), 返回请求ID, 通过轮询接口`GET /api/creative_generate/result/{request_id}`获取结果
    方式二: wait_result=True 接口阻塞, 知道结果返回为止并返回生成结果
    parmas:
        prompt: str 必选, 用于对图像生成主体,风格等描述
        instructions: str 可选, 用于覆盖默认的指令
        parameter: dict | None, 用于控制效果, 比如aspect: 图片宽高比, tile 是否无缝纹理(四方连续)
        wait_result: bool 可选, 接口是否等待结果, 默认False,

    :return:
    """
    if not params.request_id:
        params.request_id = unique_id()

    if not params.texture_id and not all([params.prompt, params.parameter]):
        return {"code": 400, "message": "参数不完整", "data": {}}
    if params.texture_id:
        stmt = select(PatternPreset).where(PatternPreset.id == params.texture_id)
        texture: PatternPreset | None = db.execute(stmt).scalars().one_or_none()
        default = dict(
            default_prompt=", ".join(texture.prompt) if texture.prompt else "",
            instructions=texture.instructions,
            default_parameter=texture.parameters,
        )
    else:
        instructions = (
            params.instructions
            if params.instructions
            else settings.default_instructions
        )
        default = dict(instructions=instructions)

    imagine_prompt = ImaginePrompt(**params.model_dump(exclude_unset=True), **default)
    # imagine_prompt = ImaginePrompt(**task_dict["data"], **default)
    prompt = await handle_imagine_prompt(imagine_prompt)

    await rate_limiter.wait()

    sf = Snowflake.parse(1225001209962692608, 1420070400000)
    gen = SnowflakeGenerator.from_snowflake(sf)
    nonce = str(next(gen))
    logger.info(
        f"Send imagine task to midjourney bot(discord channel). "
        f"channel_id: {settings.channel_id}, request_id: {imagine_prompt.request_id}, nonce: {nonce}"
    )

    await imagine(prompt, nonce)
    if params.wait_result:
        # 等待结果
        pass
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=settings.wait_max_seconds)
        while datetime.now() < end_time:
            result = await cache.get(
                f"{settings.redis_texture_generation_result}:{params.request_id}"
            )
            if result:
                try:
                    result = json.loads(result)
                    data = result["data"]["images"]
                    return {
                        "code": 200,
                        "message": "获取结果成功",
                        "data": {
                            "wait_result": True,
                            "images": data,
                            "request_id": params.request_id,
                        },
                    }
                except json.JSONDecodeError:
                    return {
                        "code": 400,
                        "message": "解析结果失败",
                        "data": None,
                    }
            logger.debug("轮询结果中...")
            time.sleep(10)
            pass

        return
    return {
        "code": 200,
        "message": "图像任务创建成功",
        "data": {
            "request_id": params.request_id,
            "wait_result": False,
        },
    }
    ...


class TextureOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )
    name: str = Field(..., description="纹理名称")
    prompt: list[str] | None = Field(None, description="提示词")
    instructions: str | None = Field(None, description="说明")
    parameters: list[str] | None = Field(None, description="参数")


@router.get("/creative_generate/preset", summary="获取预设纹理")
async def get_preset_texture(
    db: Session = Depends(get_db),
):
    """
    获取预设纹理, 通过传入预设配置id来实现不同的生成风格, 避免用户自己来对风格进行约束
    :return:
    """
    stmt = select(PatternPreset)
    textures: Sequence[PatternPreset] = db.execute(stmt).scalars().all()
    return {
        "code": 200,
        "message": "获取预设纹理成功",
        "data": [TextureOut.model_validate(texture) for texture in textures],
    }


@router.get("/creative_generate/result/{request_id}", summary="获取创意生成结果")
async def get_generate(
    request_id: str,
    cache: Redis = Depends(get_redis_cache),
):
    """
    接口用于前端轮询, 自定义最大时间后停止获取结果并报错

    """
    result = await cache.get(f"{settings.redis_texture_generation_result}:{request_id}")
    if not result:
        return {"code": 404, "message": "未找到结果", "data": {}}
    try:
        result = json.loads(result)
        data = result["data"]["images"]
        return {
            "code": 200,
            "message": "获取结果成功",
            "data": {
                "images": data,
                "request_id": request_id,
            },
        }
    except json.JSONDecodeError:
        return {
            "code": 400,
            "message": "解析结果失败",
            "data": None,
        }
