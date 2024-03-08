from typing import List

from pydantic import BaseModel


class ImagineBase(BaseModel):
    prompt: str


class Imagine(ImagineBase):
    ...


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

    trigger_id: str
