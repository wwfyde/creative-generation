from typing import List

from pydantic import BaseModel, HttpUrl


class ImagineBase(BaseModel):
    prompt: str


class ImagineParameter(BaseModel):
    aspect: str | None = '1:1'
    texture_id: int | None = None
    chaos: int | None = None
    style_reference: str | None = None
    character_reference: str | None = None
    quality: int | None = None
    style: str | None = None
    stylize: int | None = None
    relax: bool | None = None
    turbo: bool | None = None
    seed: int | None = None
    tile: bool | None = None
    video: bool | None = None
    version: int | float | None = None


class ImagineSubstitution(BaseModel):
    subject: str | None = None
    background: str | None = None
    texture: str | None = None
    style: str | None = None


class ImaginePrompt(ImagineBase):
    request_id: int
    prompt: str
    tags: List[str] | None = None
    substitution: ImagineSubstitution | None = None
    parameter: ImagineParameter | None = None

    ...


class ImagineTaskData(BaseModel):
    # TODO 参数验证
    request_id: int | str

    ...


class ImagineTask(BaseModel):
    request_id: str | int
    data: str


class Attachment(BaseModel):
    id: int
    url: str
    proxy_url: str
    filename: str
    content_type: str
    width: int
    height: int
    size: int
    ephemeral: bool


class EmbedsImage(BaseModel):
    url: str
    proxy_url: str


class Embed(BaseModel):
    type: str
    description: str
    image: EmbedsImage


class CallbackData(BaseModel):
    type: str
    id: int
    content: str
    attachments: List[Attachment]
    embeds: List[Embed]
    url: HttpUrl

    request_id: str | int


class GenerateResponse(BaseModel):
    images: List[str]
    request_id: str | int
    task_id: str
    sub_task_id: str
    mq_params_id: str
