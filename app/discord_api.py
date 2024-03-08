import logging
from typing import Dict, Any

import httpx

from app import settings

MESSAGE_URL = f"https://discord.com/api/v9/channels/{settings.channel_id}/messages"


def handle_payload(type_: int, app_cmd: dict, extra_params: dict) -> dict:
    # 通用参数
    payload = {
        "type": type_,
        "application_id": "936929561302675456",
        "guild_id": settings.guild_id,
        "channel_id": settings.channel_id,
        "session_id": "a826741b9ad6d6ce09b1acfe7ed5e3bb",
        "data": app_cmd  # application command object
    }
    # 额外参数
    payload.update(extra_params)
    return payload


async def handler(*,
                  method: str | None = 'post',
                  url: str,
                  header: dict,
                  command: Dict[str, Any]) -> bool | None:
    """
    通用Discord API handler
    :param method: HTTP method
    :param payload:
    :return:
    """
    logging.debug('')
    async with httpx.AsyncClient as client:
        payload = handle_payload()

        await client.request(method=method, url=url, headers=header, json=payload)

    return True


async def generate():
    """
    图像生成
    :return:
    """
    type = 2
    ...


async def ack_message():
    """

    :return:
    """


async def upscale(
        index: int,
        message_id: str,
        message_hash: str,
        extra_params: dict
):
    """
    放大增强图片
    :param index:
    :param message_id:
    :param message_hash:
    :param extra_params:
    :return:
    """
    ...
    return True


async def variation(
        index: int,
        message_id: str,
        message_hash: str,
        extra_params: dict
):
    ...


async def describe():
    """
    为图片创建描述
    :return:
    """
