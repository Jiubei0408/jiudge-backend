import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, UnicodeText, Boolean
from app.models.base import Base, db
from app.models.remote_contest import RemoteContest


class RemoteScoreboard(Base):
    __tablename__ = 'remote_scoreboard'

    fields = ['id', 'remote_contest_id', 'scoreboard_json', 'frozen', 'update_time']

    id = Column(Integer, primary_key=True, autoincrement=True)
    remote_contest_id = Column(Integer, ForeignKey(RemoteContest.id), unique=True)
    scoreboard_json = Column(UnicodeText, default='')
    frozen = Column(Boolean, nullable=False, default=False)
    update_time = Column(DateTime)

    @classmethod
    def create(cls, **kwargs):
        kwargs.setdefault('update_time', datetime.datetime.now())
        return super().create(**kwargs)

    @classmethod
    def get_by_remote_contest_id(cls, contest_id):
        r = cls.search(remote_contest_id=contest_id)['data']
        if r:
            return r[0]
        return None
