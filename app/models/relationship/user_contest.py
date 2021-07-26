from sqlalchemy import Column, Integer, String, ForeignKey

from app.models.base import Base, db
from app.models.user import User
from app.models.contest import Contest


class UserContestRel(Base):
    __tablename__ = 'user_contest_rel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey(User.username))
    contest_id = Column(Integer, ForeignKey(Contest.id))

    @staticmethod
    def get_users_by_contest_id(contest_id):
        return db.session.query(User). \
            filter(User.username == UserContestRel.username). \
            filter(UserContestRel.contest_id == contest_id).all()

    @staticmethod
    def delete_contest(contest_id):
        db.session.query(UserContestRel). \
            filter(UserContestRel.contest_id == contest_id). \
            delete()
