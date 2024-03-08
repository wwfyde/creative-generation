import asyncio
import json

import httpx
from fastapi import APIRouter, HTTPException, WebSocket
from loguru import logger

from app.config import settings
from app.discord_api import handle_payload
from app.schemas import Imagine
from app.worker import background_task

# from starlette.websockets import WebSocket

router = APIRouter()


async def handle_prompt(
        text: str,
        style: str | None = None
) -> str | None:
    """
    提示词翻译, 根据根据ChatGPTAPI取得标准的英文翻译
    :param text:
    :param style:
    :return:
    """
    ...
    return text


@router.post("/imagine")
async def imagine(
        prompt: Imagine
):
    # 处理提示词
    handled_prompt = await handle_prompt(prompt.prompt)
    if not handled_prompt:
        detail = f"Invalid Prompt"
        logger.error(detail)
        raise HTTPException(status_code=400, detail=detail)
    # 将任务添加到Celery队列

    # discord_api.generate()
    # r = await get_redis_connection()
    # await r.lpush('midjourney:tasks', prompt.model_dump_json())
    # TODO 异步处理任务
    command_object = {
        "version": "1166847114203123795",
        "id": "938956540159881230",
        "name": "imagine",
        "type": 1,
        "options": [
            {
                "type": 3,
                "name": "prompt",
                "value": handled_prompt
            }
        ],
        "application_command": {
            "id": "938956540159881230",
            "type": 1,
            "application_id": "936929561302675456",
            "version": "1166847114203123795",
            "name": "imagine",
            "description": "Create images with Midjourney",
            "options": [
                {
                    "type": 3,
                    "name": "prompt",
                    "description": "The prompt to imagine",
                    "required": True,
                    "description_localized": "The prompt to imagine",
                    "name_localized": "prompt"
                }
            ],
            "integration_types": [
                0
            ],
            "global_popularity_rank": 1,
            "description_localized": "Create images with Midjourney",
            "name_localized": "imagine"
        },
        "attachments": []
    }
    payload = handle_payload(2, command_object, {})
    logger.info(f"{type(payload)=}, {payload=}")
    logger.info(json.dumps(payload))
    async with httpx.AsyncClient(timeout=settings.httpx_timeout) as client:
        response = await client.post(
            url=settings.interaction_url,
            headers={
                'Authorization': settings.user_token,
                'Content-Type': 'application/json'
            },

            json=payload

        )
        response.raise_for_status()
        logger.info(response.text)
    # async with aiohttp.ClientSession(
    #         timeout=aiohttp.ClientTimeout(total=30),
    #         headers={
    #             'Authorization': settings.user_token,
    #             'Content-Type': 'application/json'
    #         }
    # ) as session:
    #     async with session.post(
    #             settings.interaction_url,
    #             json=payload
    #
    #     ) as response:
    #         # response.raise_for_status()
    #         logger.info(response.text)
    #
    return {"message": "任务已添加到队列", "data": {
        "prompt": handled_prompt,
        # "style": prompt.style,
        "task_id": ''
    }}


@router.post("/generate_message")
async def generate_message(
        prompt: str
):
    """
    轮询接口, 用于获取生成的消息
    :param prompt:
    :return:
    """
    ...


@router.websocket("/ws_imagine")
async def warning_event_server(websocket: WebSocket,
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
        # TODO 解析语音流信息, 并存储到数据库
        if data['']:
            pass
        # log.info(f"接收信息成功:{data}")
        await websocket.send_json()
        await websocket.send_text(f"Message text was: {type(data)}")
        await asyncio.sleep(settings.warning_interval)


@router.post("/create_celery_task")
async def trigger_task(name: str):
    result = background_task.delay(name)
    return {
        "message": "Task triggerred!",
        "task_id": result.id
    }


@router.get("/get_celery_task")
async def get_celery_task(task_id: str):
    result = background_task.AsyncResult(task_id)
    if result.ready():
        return {"result": result.get()}
    else:
        return {"status": "pending"}
