from sqlalchemy import Column, Integer, String, ForeignKey

from app.models.base import Base, db
from app.models.problem import Problem
from app.models.contest import Contest


class ProblemContestRel(Base):
    __tablename__ = 'problem_contest_rel'

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_id = Column(Integer, ForeignKey(Problem.id))
    contest_id = Column(Integer, ForeignKey(Contest.id))
    problem_id_in_contest = Column(String(100))

    @property
    def problem(self):
        p = Problem.get_by_id(self.problem_id)
        p.problem_id = self.problem_id_in_contest
        p.show('problem_id')
        return p

    @classmethod
    def get_by_problem_id_in_contest(cls, contest_id, problem_id):
        r = cls.search(contest_id=contest_id, problem_id_in_contest=problem_id)['data']
        if r:
            return r[0]
        return None

    @staticmethod
    def get_problems_by_contest_id(contest_id):
        problem_info_list = db.session.query(Problem, ProblemContestRel.problem_id_in_contest). \
            filter(Problem.id == ProblemContestRel.problem_id). \
            filter(ProblemContestRel.contest_id == contest_id).all()

        def change_problem_id(p, id_):
            p.problem_id = id_
            p.show('problem_id')
            return p

        return [change_problem_id(p, id_) for p, id_ in problem_info_list]

    @staticmethod
    def delete_contest(contest_id):
        db.session.query(ProblemContestRel). \
            filter(ProblemContestRel.contest_id == contest_id). \
            delete()
