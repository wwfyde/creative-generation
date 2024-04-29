from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, Boolean, DateTime, String, JSON, ForeignKey  # noqa
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship  # noqa


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
class PatternPreset(Base):
    """
    纹理, 纹理风格
    """
    __tablename__ = "pattern_preset"
    __table_args__ = {
        'comment': '纹理'
    }
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="纹理ID")
    name: Mapped[str] = mapped_column(String(128), comment="纹理名称")
    image: Mapped[str] = mapped_column(String(512), comment="图像链接")
    prompt: Mapped[List[str]] = mapped_column(JSON, comment="纹理提示")
    # is_tile: Mapped[bool] = mapped_column(Boolean, comment="是否无缝材质")
    instructions: Mapped[Optional[str]] = mapped_column(String(2048), comment="指令")
    category_id: Mapped[int] = mapped_column(ForeignKey("pattern_preset_category.id"))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, comment="标签")
    parameters: Mapped[Optional[List[str]]] = mapped_column(JSON, comment="命令参数")
    # aspect: Mapped[Optional[str]] = mapped_column(String(12), comment="图像宽高比")
    description: Mapped[Optional[str]] = mapped_column(String(1024), comment="风格描述")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, comment="更新时间")


class PatternPresetCategory(Base):
    __tablename__ = "pattern_preset_category"
    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment="纹理类别ID")
    name: Mapped[str] = mapped_column(String(128), comment="纹理类别")
    # pattern_presets: Mapped["PatternPreset"] = relationship(back_populates="pattern_preset_category")
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


class LLM(Base):
    __tablename__ = "llm"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment="模型名称")
    description: Mapped[str] = mapped_column(String(500), nullable=True, comment="详细说明")
    provider: Mapped[str] = mapped_column(String(50), nullable=True, comment='供应商')
    base_url: Mapped[str] = mapped_column(String(100), nullable=True, comment='基础URL')
    api_key: Mapped[str] = mapped_column(String(100), nullable=False, comment='API Key')
    models: Mapped[JSON] = mapped_column(JSON, nullable=True, comment="模型列表")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=True, comment='创建时间')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now,
                                                 onupdate=datetime.now, nullable=True, comment='更新时间')
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
