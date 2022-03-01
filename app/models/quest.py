from app.models.base import Base
from sqlalchemy import Column, Integer, String, Enum, Text
from app.libs.enumerate import QuestStatus, QuestType


class Quest(Base):
    __tablename__ = 'quest'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(200), default='')
    time_stamp = Column(Integer)
    status = Column(Enum(QuestStatus), default=QuestStatus.INQUEUE)
    message = Column(Text, default='')
    type = Column(Enum(QuestType), nullable=False)
    relation_data_id = Column(Integer)
