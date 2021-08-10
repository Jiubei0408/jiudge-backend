from sqlalchemy import Column, Integer, String, ForeignKey, Text, or_, desc

from app.models.base import Base, db

from app.models.contest import Contest
from app.models.problem import Problem
from app.models.user import User
from app.models.relationship.problem_contest import ProblemContestRel


class Clarification(Base):
    __tablename__ = 'clarification'
    fields = ['id', 'who', 'to', 'problem_id_in_contest', 'content']

    id = Column(Integer, primary_key=True, autoincrement=True)
    _who = Column('who', String(100), ForeignKey(User.username), nullable=False)
    _to = Column('to', String(100), ForeignKey(User.username))
    contest_id = Column(Integer, ForeignKey(Contest.id))
    problem_id = Column(Integer, ForeignKey(Problem.id))
    content = Column(Text, default='')

    @property
    def who(self):
        return User.get_by_id(self._who)

    @who.setter
    def who(self, user):
        self._who = user.username

    @property
    def to(self):
        return User.get_by_id(self._to)

    @to.setter
    def to(self, user):
        self._to = user.username

    @property
    def problem_id_in_contest(self):
        if self.problem_id is None:
            return None
        return ProblemContestRel. \
            get_by_problem_id_and_contest_id(self.contest_id, self.problem_id).problem_id_in_contest

    @classmethod
    def search_by_contest_id(cls, contest_id, page=1, page_size=20):
        res = db.session.query(Clarification)
        from flask_login import current_user
        if current_user.is_anonymous:
            res = res.filter(Clarification._to.is_(None))
        elif not Contest.get_by_id(contest_id).is_admin(current_user):
            res = res.filter(
                or_(
                    Clarification._to == current_user.username,
                    Clarification._who == current_user.username,
                    Clarification._to.is_(None)
                )
            )
        res = res.order_by(desc(Clarification.id))
        data = {
            'meta': {
                'count': res.count(),
                'page': page,
                'page_size': page_size
            }
        }
        if page_size != -1:
            res = res.offset((page - 1) * page_size).limit(page_size)
        res = res.all()
        data['data'] = res
        return data
