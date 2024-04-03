"""
Discord Midjourney Bot API, 通过API模拟与Midjourney进行交互
"""
import string
import time

import httpx
import redis.asyncio as redis
from loguru import logger

from app import settings
from app.schemas import CallbackData, ImaginePrompt
from app.utils import translate_by_azure, translate_by_kimi

# 获取消息
MESSAGE_URL = f"https://discord.com/api/v9/channels/{settings.channel_id}/messages"

# 回调函数 通知生成任务完成
CALLBACK_URL = f"http://localhost:8000{settings.api_prefix}/imagine/callback"
proxies = {
    "http://": settings.proxy_url,
    "https://": settings.proxy_url
}


async def handle_imagine_prompt(imagine_prompt: ImaginePrompt, **kwargs) -> str | None:
    """
    提示词翻译, 根据根据ChatGPTAPI取得标准的英文翻译
    :return:
    """
    # 获取trigger_id 用于标记任务

    # 将提示词翻译为英文
    logger.debug(f"待翻译消息: {imagine_prompt.prompt=}")
    logger.debug(f"基础提示词: {imagine_prompt.default_prompt=}")
    if imagine_prompt.prompt:
        start = time.time()
        instruction = imagine_prompt.instructions if imagine_prompt.instructions is not None else settings.default_instructions
        logger.info(f"大模型指令(llm instruction): {instruction}")
        instruction = string.Template(instruction).safe_substitute(prompt=imagine_prompt.default_prompt)
        try:
            user_prompt = await translate_by_azure(f"{imagine_prompt.default_prompt}\n\n{imagine_prompt.prompt}",
                                                   instruction)
        except Exception as exc:
            user_prompt = ""
        logger.info(f"通过Azure OpenAI翻译prompt, 翻译结果: {user_prompt}")
        # user_prompt = imagine_prompt.prompt
        if user_prompt is None:
            logger.error("Azure翻译异常, 使用月之暗面Moonshot(Kimi) API")
            logger.debug(f"用户提示词: {imagine_prompt.prompt}, 指令: {instruction}")
            try:
                user_prompt = await translate_by_kimi(f"{imagine_prompt.default_prompt}\n\n{imagine_prompt.prompt}",
                                                      instruction)
            except Exception as exc:
                user_prompt = ""
        logger.info(f"调用翻译API耗时: {(time.time() - start):.3f}秒")
    else:
        logger.error("提示词不存在, 使用默认提示词")
        user_prompt = ""
    logger.debug(f"{user_prompt=}")

    params = imagine_prompt.default_parameter if imagine_prompt.default_parameter else []
    # 组装参数
    for key, value in imagine_prompt.parameter.model_dump(exclude_unset=True).items():
        if isinstance(value, bool) and value:
            params.append(f"--{key}")
        elif isinstance(value, bool) and value is False:
            # 删除该参数
            if f"--{key}" in params:
                params.remove(f"--{key}")
            pass

        else:
            # 应该将参数添加到列表开头, 开头具有更高的优先级
            params.insert(0, f"--{key} {value}")
    # params.append('--relax')
    params_str = ' '.join(params)
    logger.debug(f"{params_str=}")

    # # 从数据库中获取风格
    # with Session(engine) as session:
    #     texture = session.get(Texture, imagine_prompt.style_id)
    # 提示词格式 <#request_id#> prompt parameters

    if not user_prompt:
        user_prompt = imagine_prompt.default_prompt
    return f"{settings.prompt_prefix}{imagine_prompt.request_id}{settings.prompt_suffix} {user_prompt}. {params_str}"


async def callback(data: CallbackData, r: redis.Redis) -> None:
    """
    回调函数, 当图片生成完成后, 向接口发送通知, 需要前端或提供推送地址
    :param data:
    :param r:
    :return:
    """
    # 将生成的图片存入redis
    resp = await r.set(f"{settings.redis_texture_generation_result}:{data.request_id}",
                       data.model_dump_json(),
                       ex=settings.redis_expire_time
                       )
    logger.info(f"request_id: {data.request_id}, 生成成功: 图片链接: {data.url}")

    # logger.debug(f"callback data: {data}")
    #
    # if not CALLBACK_URL:
    #     return
    #
    # headers = {"Content-Type": "application/json"}
    # async with httpx.AsyncClient(
    #         timeout=settings.httpx_timeout,
    #         headers=headers
    # ) as client:
    #     await client.post(CALLBACK_URL, json=data.model_dump())


def handle_payload(type_: int, nonce: str, data: dict, extra_params: dict = None) -> dict:
    """
    payload 处理
    :param type_:
    :param nonce:
    :param data:
    :param extra_params:
    :return:
    """
    payload = {
        "type": type_,
        "application_id": settings.application_id,
        "guild_id": settings.guild_id,
        "channel_id": settings.channel_id,
        "session_id": settings.session_id,
        "data": data,  # application command object
        "nonce": nonce,
    }
    # 处理额外参数
    if extra_params:
        payload.update(extra_params)
    return payload


async def imagine(prompt: str, nonce: str) -> bool:
    """
    /imagine prompt
    {"type":2,"application_id":"936929561302675456","guild_id":"1076097007850111017","channel_id":"1076097007850111020","session_id":"aa6cd72b34ccb37e8b615dc4f9688da7","data":{"version":"1166847114203123795","id":"938956540159881230","name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":"the legend of Big Foot yeti by Joan Cornella, \"BELIEVE\" written on top  --style  raw  --ar  5:7  --stylize  25"}],"application_command":{"id":"938956540159881230","type":1,"application_id":"936929561302675456","version":"1166847114203123795","name":"imagine","description":"Create images with Midjourney","options":[{"type":3,"name":"prompt","description":"The prompt to imagine","required":true,"description_localized":"The prompt to imagine","name_localized":"prompt"}],"dm_permission":true,"integration_types":[0],"global_popularity_rank":1,"description_localized":"Create images with Midjourney","name_localized":"imagine"},"attachments":[]},"nonce":"1224974236855042048","analytics_location":"slash_ui"}

    {
  "type": 2,
  "guild_id": "$guild_id",
  "channel_id": "$channel_id",
  "application_id": "936929561302675456",
  "session_id": "$session_id",
  "nonce": "$nonce",
  "data": {
    "version": "1166847114203123795",
    "id": "938956540159881230",
    "name": "imagine",
    "type": 1,
    "options": [
      {
        "type": 3,
        "name": "prompt",
        "value": "$prompt"
      }
    ]
  }
}
    :return:
    """
    data = {
        "version": "1166847114203123795",
        "id": "938956540159881230",
        "name": "imagine",
        "type": 1,
        "options": [
            {
                "type": 3,
                "name": "prompt",
                "value": prompt
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
            "dm_permission": True,
            "integration_types": [
                0
            ],
            "global_popularity_rank": 1,
            "description_localized": "Create images with Midjourney",
            "name_localized": "imagine"
        },
        "attachments": [],
        # "application_command": {
        #     "id": "938956540159881230",
        #     "type": 1,
        #     "application_id": settings.application_id,
        #     "version": "1166847114203123795",
        #     "name": "imagine",
        #     "description": "Create images with Midjourney",
        #     "options": [
        #         {
        #             "type": 3,
        #             "name": "prompt",
        #             "description": "The prompt to imagine",
        #             "required": True,
        #             "description_localized": "The prompt to imagine",
        #             "name_localized": "prompt"
        #         }
        #     ],
        #     "integration_types": [
        #         0
        #     ],
        #     "global_popularity_rank": 1,
        #     "description_localized": "Create images with Midjourney",
        #     "name_localized": "imagine"
        # },
        # "attachments": []
    }
    payload = handle_payload(2, nonce, data, {})
    logger.debug(payload)
    print(payload)
    async with httpx.AsyncClient(timeout=settings.httpx_timeout, proxies=proxies) as client:
        response = await client.post(
            url=settings.interaction_url,
            headers={
                'Authorization': settings.user_token,
                'Content-Type': 'application/json'
            },

            json=payload

        )
        logger.info(response.text)
        if response.status_code in range(200, 300):
            logger.info("分发任务成功")
            logger.debug(f"{response.status_code=}{response.content=}")
            # 初始化result_queue

            return True
        else:
            logger.error("分发任务失败")
            return False


async def ack_message(filename: str) -> str | None:
    """
    通过Discord message API 获取生成图像
    :return:
    """


async def upscale(
        index: int,
        message_id: str,
        message_hash: str,
        extra_params: dict
):
    """
    放大增强图片, U1, U2, U3, U4
    其实是图像分割
    :param index:
    :param message_id:
    :param message_hash:
    :param extra_params:
    :return:
    """
    ...

    # 根据message_id
    url = "https://discord.com/api/v9/interactions"

    payload_2 = {
        "type": 3,
        "nonce": "1216567644111503360",
        "guild_id": "1076097007850111017",
        "channel_id": "1076097007850111020",
        "message_flags": 0,
        "message_id": "1216371139681456158",
        "application_id": "936929561302675456",
        "session_id": "faa9c3fcd1bb335c22a3eb49d78bddf4",
        "data": {
            "component_type": 2,
            "custom_id": "MJ::JOB::upsample::2::e68e4d8b-77ea-4c8f-9589-72f3a8c0bfd0"
        }
    }
    payload_3 = {
        "type": 3, "nonce": "1216568420791746560",
        "guild_id": "1076097007850111017",
        "channel_id": "1076097007850111020", "message_flags": 0, "message_id": "1216371139681456158",
        "application_id": "936929561302675456", "session_id": "faa9c3fcd1bb335c22a3eb49d78bddf4",
        "data": {"component_type": 2,
                 "custom_id": "MJ::JOB::upsample::3::e68e4d8b-77ea-4c8f-9589-72f3a8c0bfd0"}}
    return True


async def subtle_upscale(
        image_index: int,
):
    """
    精细放大
    :param image_index:
    :return:
    """
    ...
    url = "https://discord.com/api/v9/interactions"
    message = "<#32345#> a asia girl with long and black and straight hair --style raw --v 6.0 - Upscaled (Subtle) by @xhcyw2 (fast)"
    token = " Upscaled (Subtle) "
    payload = {"type": 3, "nonce": "1216564633255542784", "guild_id": "1076097007850111017",
               "channel_id": "1076097007850111020", "message_flags": 0, "message_id": "1216372243345571871",
               "application_id": "936929561302675456", "session_id": "faa9c3fcd1bb335c22a3eb49d78bddf4",
               "data": {"component_type": 2,
                        "custom_id": "MJ::JOB::upsample_v6_2x_subtle::1::fc9b0549-969a-437f-8949-c6defa2be2a1::SOLO"}}


async def creative_upscale(
        image_index: int,
):
    """
    创意放大
    :param image_index:
    :return:
    """
    ...
    # message = "<#32345#> a asia girl with long and black and straight hair --style raw --v 6.0 - Upscaled (Creative) by @xhcyw2 (fast)"
    token = " Upscaled (Creative) "
    payload = {"type": 3,
               "nonce": "1216562088659386368", "guild_id": "1076097007850111017",
               "channel_id": "1076097007850111020", "message_flags": 0, "message_id": "1216372243345571871",
               "application_id": "936929561302675456", "session_id": "faa9c3fcd1bb335c22a3eb49d78bddf4",
               "data": {"component_type": 2,
                        "custom_id": "MJ::JOB::upsample_v6_2x_creative::1::fc9b0549-969a-437f-8949-c6defa2be2a1::SOLO"}}
    special_token = "custom_id"


async def variation(
        index: int,
        message_id: str,
        message_hash: str,
        extra_params: dict
):
    ...


async def describe():
    """
    为图像创建描述
    form-data
    {"type":2,"application_id":"936929561302675456","guild_id":"1076097007850111017","channel_id":"1076097007850111020","session_id":"002bfe88bc266348b0eb0a7affcf68fe","data":{"version":"1204231436023111690","id":"1092492867185950852","name":"describe","type":1,"options":[{"type":11,"name":"image","value":0}],"application_command":{"id":"1092492867185950852","type":1,"application_id":"936929561302675456","version":"1204231436023111690","name":"describe","description":"Writes a prompt based on your image.","options":[{"type":11,"name":"image","description":"The image to describe","required":false,"description_localized":"The image to describe","name_localized":"image"},{"type":3,"name":"link","description":"…","required":false,"description_localized":"…","name_localized":"link"}],"integration_types":[0],"global_popularity_rank":3,"description_localized":"Writes a prompt based on your image.","name_localized":"describe"},"attachments":[{"id":"0","filename":"7811e9f022e9484b9b80991abbfdcfad.jpeg","uploaded_filename":"ad057382-3771-4d62-b847-1adbec12a899/7811e9f022e9484b9b80991abbfdcfad.jpeg"}]},"nonce":"1217645936977641472","analytics_location":"slash_ui"}
    :return:
    """
    payload = {"type": 2,
               "application_id": settings.application_id,
               "guild_id": settings.guild_id,
               "channel_id": settings.channel_id,
               "session_id": "002bfe88bc266348b0eb0a7affcf68fe",
               "data": {
                   "version": "1204231436023111690",
                   "id": "1092492867185950852", "name": "describe", "type": 1,
                   "options": [{"type": 11, "name": "image", "value": 0}],
                   "application_command": {
                       "id": "1092492867185950852", "type": 1,
                       "application_id": "936929561302675456",
                       "version": "1204231436023111690",
                       "name": "describe",
                       "description": "Writes a prompt based on your image.", "options": [
                           {"type": 11, "name": "image", "description": "The image to describe", "required": False,
                            "description_localized": "The image to describe", "name_localized": "image"},
                           {"type": 3, "name": "link", "description": "…", "required": False,
                            "description_localized": "…", "name_localized": "link"}], "integration_types": [0],
                       "global_popularity_rank": 3,
                       "description_localized": "Writes a prompt based on your image.",
                       "name_localized": "describe"
                   },
                   "attachments": [
                       {"id": "0", "filename": "7811e9f022e9484b9b80991abbfdcfad.jpeg",
                        "uploaded_filename": "ad057382-3771-4d62-b847-1adbec12a899/7811e9f022e9484b9b80991abbfdcfad.jpeg"}
                   ]
               },
               "nonce": "1217645936977641472", "analytics_location": "slash_ui"}

    ...


async def turbo():
    """
    加速图像生成
    通过表单格式上传json文件
    {"type":2,"application_id":"936929561302675456","guild_id":"1076097007850111017","channel_id":"1076097007850111020","session_id":"5bb831fad8ed93e2aeed9b7b4f1a37d2","data":{"version":"1124132684143271997","id":"1124132684143271996","name":"turbo","type":1,"options":[],"application_command":{"id":"1124132684143271996","type":1,"application_id":"936929561302675456","version":"1124132684143271997","name":"turbo","description":"Switch to turbo mode","integration_types":[0],"global_popularity_rank":18,"options":[],"description_localized":"Switch to turbo mode","name_localized":"turbo"},"attachments":[]},"nonce":"1217311770322927616","analytics_location":"slash_ui"}
    """
    ...


async def fast():
    """
    {"type":2,"application_id":"936929561302675456","guild_id":"1076097007850111017","channel_id":"1076097007850111020","session_id":"e587ddde4e5f1018987df676adf9cd52","data":{"version":"987795926183731231","id":"972289487818334212","name":"fast","type":1,"options":[],"application_command":{"id":"972289487818334212","type":1,"application_id":"936929561302675456","version":"987795926183731231","name":"fast","description":"Switch to fast mode","dm_permission":true,"integration_types":[0],"global_popularity_rank":10,"options":[],"description_localized":"Switch to fast mode","name_localized":"fast"},"attachments":[]},"nonce":"1224184418860531712","analytics_location":"slash_ui"}
    """

    ...


async def relax():
    """

    """
