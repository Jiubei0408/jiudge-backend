from sqlalchemy import Column, Integer, String, ForeignKey

from app.models.base import Base
from app.models.clarification import Clarification
from app.models.user import User


class UserClarRead(Base):
    __tablename__ = 'user_clar_read'

    username = Column(String(100), ForeignKey(User.username), primary_key=True)
    clar_id = Column(Integer, ForeignKey(Clarification.id), primary_key=True)

    @classmethod
    def get_by_username_and_clar_id(cls, username, clar_id):
        r = cls.search(username=username, clar_id=clar_id)['data']
        if r:
            return r[0]
        return None
