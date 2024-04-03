import asyncio
import io
import time
import uuid
from pathlib import PurePath
from typing import List

import httpx
import oss2
import requests
from PIL import Image
from fastapi import HTTPException
from loguru import logger
from openai import OpenAI
from pydantic import DirectoryPath
from requests.adapters import HTTPAdapter
from tenacity import retry, wait_fixed, stop_after_attempt
from urllib3 import Retry

from app import settings


def gen_uuid(return_type: str = 'str') -> str | int:
    match return_type:
        case 'str':
            uid = str(uuid.uuid4())
        case "int":
            uid = uuid.uuid4().int
        case "hex":
            uid = uuid.uuid4().hex
        case _:
            uid = uuid.uuid4().hex

    return uid


def split_image(image_file):
    with Image.open(image_file) as im:
        # Get the width and height of the original image
        width, height = im.size
        # Calculate the middle points along the horizontal and vertical axes
        mid_x = width // 2
        mid_y = height // 2
        # Split the image into four equal parts
        top_left = im.crop((0, 0, mid_x, mid_y))
        top_right = im.crop((mid_x, 0, width, mid_y))
        bottom_left = im.crop((0, mid_y, mid_x, height))
        bottom_right = im.crop((mid_x, mid_y, width, height))

        return top_left, top_right, bottom_left, bottom_right


async def download_image(
        url: str,
        directory: DirectoryPath,
        filename: str,
        is_split: bool = False,
):
    response = httpx.get(url, timeout=settings.httpx_timeout, proxies={
        "http://": settings.proxy_url,
        "https://": settings.proxy_url
    })
    # response = requests.get(url, timeout=settings.httpx_timeout)
    response.raise_for_status()
    if response.status_code == 200:

        output_folder = directory.joinpath('output')
        if not output_folder.exists():
            output_folder.mkdir(parents=True, exist_ok=True)
        input_folder = directory.joinpath('input')
        if not input_folder.exists():
            input_folder.mkdir(parents=True, exist_ok=True)
        with open(directory.joinpath(input_folder, filename), "wb+") as f:
            f.write(response.content)
        print(f"Image downloaded: {filename}")

        input_file = directory.joinpath(input_folder, filename)

        # if "UPSCALED_" not in filename:
        if is_split:
            # file_prefix = os.path.splitext(filename)[0]
            file_prefix = PurePath(filename).stem
            file_suffix = PurePath(filename).suffix
            # Split the image
            top_left, top_right, bottom_left, bottom_right = split_image(input_file)
            # Save the output images with dynamic names in the output folder
            top_left.save(directory.joinpath(output_folder, f"{file_prefix}_top_left{file_suffix}"))
            top_right.save(directory.joinpath(output_folder, f"{file_prefix}_top_right{file_suffix}"))
            bottom_left.save(directory.joinpath(output_folder, f"{file_prefix}_bottom_left{file_suffix}"))
            bottom_right.save(directory.joinpath(output_folder, f"{file_prefix}_bottom_right{file_suffix}"))

            # TODO 将四张图片上传到OSS/S2等云存储服务, 并记录到数据库
        else:
            # Rename the input file
            ...
            # directory.joinpath(input_folder, filename).rename(directory.joinpath(output_folder, filename))
        # Delete the input file
        # directory.joinpath(input_folder, filename).unlink()


async def download_image_to_oss(
        url: str,
        filename: str,
        is_split: bool = False,
        request_id: int = None
) -> List[str]:
    response = httpx.get(url, timeout=settings.httpx_timeout, proxies={
        "http://": settings.proxy_url,
        "https://": settings.proxy_url
    })
    # response = requests.get(url, timeout=settings.httpx_timeout)
    response.raise_for_status()
    if response.status_code == 200:

        # 如果需要分割, 需要先分割后上传
        if is_split:
            # file_prefix = PurePath(filename).stem.split('_')[-1]
            # file_prefix = f"{request_id}"
            file_suffix = PurePath(filename).suffix
            with Image.open(io.BytesIO(response.content)) as img:
                # Get the width and height of the original image
                width, height = img.size
                # Calculate the middle points along the horizontal and vertical axes
                mid_x, mid_y = width // 2, height // 2
                # Split the image into four equal parts
                coordinates = [
                    ("top_left", (0, 0, mid_x, mid_y)),
                    ("top_right", (mid_x, 0, width, mid_y)),
                    ("bottom_left", (0, mid_y, mid_x, height)),
                    ("bottom_right", (mid_x, mid_y, width, height)),
                ]
                image_urls = []
                for index, (position, coords) in enumerate(coordinates):
                    cropped_image = img.crop(coords)
                    img_stream = io.BytesIO()
                    cropped_image.save(img_stream, format=img.format)
                    img_stream.seek(0)
                    image_url = upload_image(
                        f"{request_id}_{position}_{index + 1}_{file_suffix}",
                        img_stream.getvalue(),
                        prefix=settings.oss_storage_path,
                        rename=False,
                        domain=settings.oss_domain
                    )
                    image_urls.append(image_url)

            return image_urls

        # 将图像保存到OSS
        file_suffix = PurePath(filename).suffix
        filename = f"{request_id}{file_suffix}"

        image_url = upload_image(
            filename,
            response.content,
            prefix=settings.oss_storage_path,
            rename=False,
            domain=settings.oss_domain
        )

        logger.info(f"上传图像生成成功, 图像链接: {image_url}")
        return [image_url]


def ask_azure_openai(image, prompt, api_key, timeout=10):
    source_name = "lora-caption-us"
    deployment_id = "lora-captions"
    api_version = "2023-12-01-preview"  # vision-preview
    quality = "low"
    url = f"https://{source_name}.openai.azure.com/openai/deployments/{deployment_id}/chat/completions?api-version={api_version}"
    data = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image,
                            "detail": f"{quality}",
                        },
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }
    headers = {"Content-Type": "application/json", "api-key": f"{api_key}"}
    # 配置重试策略
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    )  # 更新参数名
    with requests.Session() as s:
        s.mount("https://", HTTPAdapter(max_retries=retries))
        try:
            response = s.post(url, headers=headers, json=data, timeout=timeout)
            response.raise_for_status()  # 如果请求失败，将抛出 HTTPError
        except requests.exceptions.HTTPError as errh:
            return f"HTTP Error: {errh}"
        except requests.exceptions.ConnectionError as errc:
            return f"Error Connecting: {errc}"
        except requests.exceptions.Timeout as errt:
            return f"Timeout Error: {errt}"
        except requests.exceptions.RequestException as err:
            return f"OOps: Something Else: {err}"
    try:
        response_data = response.json()
        if "error" in response_data:
            return f"API error: {response_data['error']['message']}"
        caption = response_data["choices"][0]["message"]["content"]
        return caption
    except Exception as e:
        return f"Failed to parse the API response: {e}\n{response.text}"


@retry(wait=wait_fixed(3), stop=stop_after_attempt(3))
async def translate_by_azure(
        message: str,
        instructions: str,
):
    """
    通过Azure API生成场景提示词
    """
    url = settings.azure_api_url
    headers = {
        "Content-Type": "application/json",
        "api-key": settings.azure_api_key
    }

    async with httpx.AsyncClient(timeout=settings.httpx_timeout) as client:
        start_time = asyncio.get_event_loop().time()
        data = {"messages": [{"role": "system", "content": instructions, }, {"role": "user", "content": message}], }
        response = await client.post(url, json=data, headers=headers)
        end_time = asyncio.get_event_loop().time()
        # 获取接口响应时间
        logger.debug(f"{end_time - start_time=}")
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            logger.debug(data)
            message: str = data['choices'][0]['message']['content']
            print(f"Azure OpenAI处理后的消息: {message}")
            return message


@retry(wait=wait_fixed(3), stop=stop_after_attempt(3))
async def translate_by_kimi(
        message: str,
        instructions: str
):
    client = OpenAI(
        api_key=settings.kimi_api_key,
        base_url=settings.kimi_api_url
    )
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system",
             "content": instructions},
            {"role": "user", "content": message}
        ],
        # 翻译效果不理想, 降低温度, 以保证一致性
        temperature=1,

    )
    return completion.choices[0].message.content


class RateLimiter:
    """"
    example:
        rate_limiter = RateLimiter(capacity=1, rate=0.2, refill_time=0.1)
        for _ in range(10):
            await rate_limiter.wait()
            # do something
    """

    def __init__(self, capacity: int, rate: float, refill_time: float = 0.1):
        # 设置桶容量
        self.capacity = capacity
        self.tokens = capacity  # 持有tokens

        # 速率限制
        self.rate = rate  # 单位时间能够添加的令牌数
        self.refill_time = refill_time  # 检查速率
        self.last_refill_time = time.time()  # 最后一次检查时间

    def add_tokens(self):
        now = time.time()
        elapsed_time = now - self.last_refill_time
        # 超过一定时间后, 添加一个令牌
        self.tokens += elapsed_time * self.rate
        self.last_refill_time = now

        # 向令牌中添加令牌, 但不能操过容量
        self.tokens = min(self.capacity, self.tokens)
        # 重置检查时间

    async def wait(self, tokens: int = 1):
        while True:
            self.add_tokens()
            # 如果桶中有足够的令牌, 则减去令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                break
            await asyncio.sleep(self.refill_time)


def unified_api(
        message: str,
        instructions: str,
        api_key: str,
        base_url: str,
):
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system",
             "content": instructions},
            {"role": "user", "content": message}
        ],
        temperature=0.3,

    )
    return completion.choices[0].message.content


def upload_image(filename: str,
                 data: str | bytes,
                 prefix: str = 'tmp',
                 rename: bool = True,
                 domain: str = None
                 ) -> str:
    """
    上传图片到OSS
    :param filename: 文件名
    :param data: 文件内容, 二进制数据或字符串
    :param prefix: OSS路径前缀 上传到OSS的路径
    :param rename: 是否重命名, 默认为True
    :param domain: OSS域名, 默认为None时使用bucket_name+endpoint
    """
    endpoint = settings.oss_endpoint

    auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
    bucket_name = settings.oss_bucket_name
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    if rename:
        uid = uuid.uuid4()
        upload_file_name = f"{prefix}/{uid}.{filename.split('.')[-1]}"
    else:
        upload_file_name = f"{prefix}/{filename}"
    if prefix is None:
        # 临时文件, 使用OSS生命周期自动删除
        upload_file_name = f"tmp/{upload_file_name}"

    result = bucket.put_object(upload_file_name, data)
    domain = domain or settings.oss_domain
    if domain:
        image_link = f"https://{domain}/{upload_file_name}"
    else:
        image_link = f"https://{bucket_name}.{endpoint}/{upload_file_name}"
    if result.status == 200:
        return image_link
    else:
        raise HTTPException(status_code=result.status, detail=result.resp.read().decode())


if __name__ == '__main__':
    # url = upload_image('demo.text', 'hello, 世界!')
    # print(url)
    # asyncio.run(translate_by_azure("Photo of 樱花,日式,山海纹,富士山 sitting on fire", settings.azure_api_instructions))
    asyncio.run(translate_by_kimi('你好，我叫李雷，1+1等于多少？', settings.default_instructions))
    ...
