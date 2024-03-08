from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db import Base


# TODO Database Mapped class Design
class Generation(Base):
    __tablename__ = "generation"
    __table_args__ = {
        'comment': '生成状态记录表'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)


class Image(Base):
    __tablename__ = "image"
    __table_args__ = {
        'comment': '图片表'
    }
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String(255), nullable=False)


class GenerationImages(Base):
    __tablename__ = "generation_images"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    generation_id = Column(Integer, ForeignKey('generation.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('image.id'), nullable=False)
    image = relationship("Image", back_populates="generation_images")
    generation = relationship("Generation", back_populates="generation_images")
