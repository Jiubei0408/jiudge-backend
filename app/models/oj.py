from sqlalchemy import Column, Integer, String

from app.models.base import Base


class OJ(Base):
    __tablename__ = 'oj'

    fields = ['id', 'name', 'status']

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    status = Column(Integer, nullable=False, default=0)
