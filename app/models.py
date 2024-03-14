from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, Boolean, DateTime, String, JSON  # noqa
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase  # noqa


class Base(DeclarativeBase):
    ...


# TODO Database Mapped class Design
class Generation(Base):
    __tablename__ = "generation"
    __table_args__ = {
        'comment': '生成状态记录表'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="生成ID")
    status = Column(Boolean, default=False, comment="生成状态")
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


# f风格  有很多图, 标签字段
# TODO 风格表
class Texture(Base):
    """
    纹理, 纹理风格
    """
    __tablename__ = "texture"
    __table_args__ = {
        'comment': '纹理'
    }
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="纹理ID")
    name: Mapped[str] = mapped_column(String(128), comment="纹理名称")
    image: Mapped[str] = mapped_column(String(512), comment="图像链接")
    prompt: Mapped[List[str]] = mapped_column(JSON, comment="纹理提示")
    is_tile: Mapped[bool] = mapped_column(Boolean, comment="是否无缝材质")
    parameters: Mapped[Optional[List[str]]] = mapped_column(JSON, comment="命令参数")
    aspect: Mapped[Optional[str]] = mapped_column(String(12), comment="图像宽高比")
    description: Mapped[Optional[str]] = mapped_column(String(1024), comment="风格描述")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, comment="更新时间")


class Instructions(Base):
    __tablename__ = "instructions"
    __table_args__ = {
        'comment': '提示指令'
    }
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="指令ID")
    name: Mapped[str] = mapped_column(String(128), comment="指令名称")
    description: Mapped[Optional[str]] = mapped_column(String(1024), comment="指令描述")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, comment="更新时间")

# TODO
# 图像列表

#
# class TextureImage(Base):
#     __tablename__ = "texture_image"
#     __table_args__ = {
#         'comment': '纹理图像'
#     }
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     texture_id: Mapped[int] = mapped_column(ForeignKey('texture.id'), nullable=False, comment="纹理ID")
#     sub_index = Column(SmallInteger, nullable=False, comment="图像子序号")
#     url = Column(String(255), nullable=False)
#
#
# class GenerationImages(Base):
#     __tablename__ = "generation_images"
#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     generation_id = Column(Integer, ForeignKey('generation.id'), nullable=False)
#     image_id = Column(Integer, ForeignKey('image.id'), nullable=False)
#     image = relationship("Image", back_populates="generation_images")
#     generation = relationship("Generation", back_populates="generation_images")
