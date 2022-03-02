from sqlalchemy import Column, Integer, String, Enum, Text

from app.libs.enumerate import QuestStatus, QuestType
from app.models.base import Base


class Quest(Base):
    __tablename__ = 'quest'

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(200), default='')
    time_stamp = Column(Integer)
    status = Column(Enum(QuestStatus), default=QuestStatus.INQUEUE)
    message = Column(Text, default='')
    type = Column(Enum(QuestType), nullable=False)
    relation_data_id = Column(Integer)

    @classmethod
    def get_by_type_and_data_id(cls, type_, data_id):
        r = cls.search(type=type_, relation_data_id=data_id)['data']
        if r:
            return r[0]
        return None
