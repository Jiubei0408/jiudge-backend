from sqlalchemy import Column, Integer, String, ForeignKey

from app.models.base import Base, db

from app.models.relationship.problem_contest import ProblemContestRel


class Clarification(Base):
    __tablename__ = 'clarification'
    fields = ['problem_id', 'content']

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_problem_id = Column(Integer, ForeignKey(ProblemContestRel.id))
    content = Column(String(1000))

    @property
    def problem_id(self):
        return ProblemContestRel.get_by_id(self.contest_problem_id).problem_id_in_contest

    @staticmethod
    def get_by_contest_id(contest_id):
        return Clarification.query.filter(
            Clarification.contest_problem_id.in_(
                db.session.query(ProblemContestRel.id).filter(
                    ProblemContestRel.contest_id == contest_id
                ).subquery()
            )
        ).all()
