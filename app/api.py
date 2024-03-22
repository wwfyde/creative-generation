import asyncio
import hashlib
from datetime import time
from typing import List, Dict

from fastapi import APIRouter, WebSocket
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.dependency import DBSession
from app.discord_api import handle_imagine_prompt
from app.models import PatternPreset
from app.schemas import ImaginePrompt
from app.worker import background_task

# from starlette.websockets import WebSocket


router = APIRouter()


def unique_id():
    """生成唯一的 10 位数字，作为任务 ID"""
    return int(hashlib.sha256(str(time()).encode("utf-8")).hexdigest(), 16) % 10 ** 10


async def imagine(
        prompt: ImaginePrompt
):
    # 处理提示词
    handled_prompt = await handle_imagine_prompt(prompt.prompt)
    # 将任务添加到Celery队列

    # discord_api.generate()
    # r = await get_redis_connection()
    # await r.lpush('midjourney:tasks', prompt.model_dump_json())
    # TODO 异步处理任任务, 而不是直接将请求发送到midjourney bot

    return {"message": "任务已添加到队列", "data": {
        "prompt": handled_prompt,
        # "style": prompt.style,
        "task_id": ''
    }}


@router.post("/imagine")
async def imagine_api(prompt: ImaginePrompt):
    await imagine(prompt)


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


@router.get('/db')
async def db_get(
        # db: Annotated[Session, Depends(get_db)]
        db: DBSession

):
    texture = db.get(PatternPreset, 1)

    return texture


@router.get("/html")
async def get():
    return HTMLResponse(html)


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
async def websocket_endpoint(
        websocket: WebSocket,
        trigger_id: str
):
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
        if data['']:
            pass
        # log.info(f"接收信息成功:{data}")
        await websocket.send_json({"message": "接收信息成功", "data": data})
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
    """
    通过任务ID轮询处理状态
    :param task_id:
    :return:
    """
    result = background_task.AsyncResult(task_id)
    if result.ready():
        return {"result": result.get()}
    else:
        return {"status": "pending"}
