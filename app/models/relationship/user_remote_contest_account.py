# 限制在某些比赛中某个用户只能通过某个vjudge账号提交

from sqlalchemy import Column, Integer, String, ForeignKey

from app.models.base import Base
from app.models.remote_contest import Contest
from app.models.user import User


class UserRemoteContestAccount(Base):
    __tablename__ = 'user_remote_contest_account'
    username = Column(String(100), ForeignKey(User.username), primary_key=True)
    contest_id = Column(Integer, ForeignKey(Contest.id), primary_key=True)
    account = Column(String(100))

    @classmethod
    def get_limited_account(cls, username, contest_id):
        r = cls.search(username=username, contest_id=contest_id)['data']
        if r:
            return r[0].account
        from app.models.relationship.user_remote_contest_oj_account import UserRemoteContestOJAccount
        contest = Contest.get_by_id(contest_id)
        r = UserRemoteContestOJAccount.search(username=username, oj_id=contest.remote_contest.oj_id)['data']
        if r:
            return r[0].account
        return None
