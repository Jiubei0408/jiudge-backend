from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey
from app.models.base import Base, db
from app.models.contest import Contest
from app.models.oj import OJ


# 远程同步赛
class RemoteContest(Base):
    __tablename__ = 'remote_contest'

    id = Column(Integer, primary_key=True, autoincrement=True)
    oj_id = Column(Integer, ForeignKey(OJ.id))
    remote_contest_id = Column(String(100))
    contest_id = Column(Integer, ForeignKey(Contest.id))

    @property
    def oj(self):
        return OJ.get_by_id(self.oj_id)

    @classmethod
    def create(cls, **kwargs):
        from app.models.remote_scoreboard import RemoteScoreboard
        r = super().create(**kwargs)
        remote_scoreboard = RemoteScoreboard.create(remote_contest_id=r.id)
        from app.services.contest import create_crawl_remote_scoreboard_schedule
        create_crawl_remote_scoreboard_schedule(remote_scoreboard.id, r)
        return r

    @property
    def contest(self):
        return Contest.get_by_id(self.contest_id)

    def delete(self):
        from app.models.remote_scoreboard import RemoteScoreboard
        RemoteScoreboard.get_by_remote_contest_id(self.id).delete()

    @classmethod
    def get_by_contest_id(cls, contest_id):
        r = cls.search(contest_id=contest_id)['data']
        if r:
            return r[0]
        return None
