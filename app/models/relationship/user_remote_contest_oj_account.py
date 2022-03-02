# 限制在某些OJ的比赛中某个用户只能通过某个vjudge账号提交

from sqlalchemy import Column, Integer, String, ForeignKey

from app.models.base import Base
from app.models.oj import OJ
from app.models.user import User


class UserRemoteContestOJAccount(Base):
    __tablename__ = 'user_remote_contest_oj_account'
    username = Column(String(100), ForeignKey(User.username), primary_key=True)
    oj_id = Column(Integer, ForeignKey(OJ.id), primary_key=True)
    account = Column(String(100))
