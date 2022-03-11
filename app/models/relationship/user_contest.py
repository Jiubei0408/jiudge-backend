from sqlalchemy import Column, Integer, String, ForeignKey, Enum

from app.libs.enumerate import ContestRegisterType
from app.models.base import Base, db
from app.models.contest import Contest
from app.models.user import User


class UserContestRel(Base):
    __tablename__ = 'user_contest_rel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey(User.username))
    contest_id = Column(Integer, ForeignKey(Contest.id))
    type = Column(Enum(ContestRegisterType), default=ContestRegisterType.Participant)

    @staticmethod
    def get_by_contest_id(contest_id):
        return db.session.query(UserContestRel). \
            filter(UserContestRel.contest_id == contest_id).all()

    @staticmethod
    def get_by_username_and_contest_id(username, contest_id):
        return db.session.query(UserContestRel). \
            filter(UserContestRel.username == username). \
            filter(UserContestRel.contest_id == contest_id).one()

    @staticmethod
    def delete_contest(contest_id):
        db.session.query(UserContestRel). \
            filter(UserContestRel.contest_id == contest_id). \
            delete()

    @property
    def user(self):
        return User.get_by_id(self.username)
