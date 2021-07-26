import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UnicodeText, Boolean
from app.models.base import Base, db
from app.models.contest import Contest


class Scoreboard(Base):
    __tablename__ = 'scoreboard'

    fields = ['contest_id', 'scoreboard_json', 'frozen', 'update_time']

    contest_id = Column(Integer, ForeignKey(Contest.id), primary_key=True)
    scoreboard_json = Column(UnicodeText, default='')
    frozen = Column(Boolean, nullable=False, default=False)
    update_time = Column(DateTime)

    @classmethod
    def create(cls, **kwargs):
        kwargs.setdefault('update_time', datetime.datetime.now())
        return super().create(**kwargs)

    @classmethod
    def get_by_contest_id(cls, contest_id):
        r = cls.search(contest_id=contest_id)['data']
        if r:
            return r[0]
        return None
