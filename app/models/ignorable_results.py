from sqlalchemy import Column, Enum

from app.libs.enumerate import JudgeResult
from app.models.base import Base


class IgnorableResults(Base):
    __tablename__ = 'ignorable_results'

    result = Column(Enum(JudgeResult), primary_key=True)

    @classmethod
    def all(cls):
        return [i.result for i in cls.search_all()['data']]
