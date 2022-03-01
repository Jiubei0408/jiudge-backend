import datetime

from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey, Float, Text, orm
from app.models.base import Base
from app.models.problem import Problem
from app.libs.enumerate import JudgeResult
from app.models.contest import Contest
from app.models.user import User
from app.models.quest import Quest


class Submission(Base):
    __tablename__ = 'submission'
    fields = ['id', 'user', 'problem', 'remote_result', 'view_result', 'code', 'lang', 'time_used', 'memory_used', 'compile_info', 'submit_time']

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey(User.username))
    problem_id = Column(Integer, ForeignKey(Problem.id))
    result = Column(Enum(JudgeResult), default=JudgeResult.PENDING)
    code = Column(Text)
    lang = Column(String(50))
    remote_result = Column(String(50), default='')
    time_used = Column(Integer, default=0)  # 单位毫秒
    memory_used = Column(Float, default=0)  # 单位kb
    compile_info = Column(Text, default='')
    submit_time = Column(DateTime)
    contest_id = Column(Integer, ForeignKey(Contest.id))

    @orm.reconstructor
    def __init__(self):
        self.secret = True

    def show_secret(self):
        self.secret = False

    def hide_secret(self):
        self.secret = True

    @property
    def view_result(self):
        return self.result.name

    @property
    def contest(self):
        return Contest.get_by_id(self.contest_id)

    @property
    def user(self):
        return User.get_by_id(self.username)

    @property
    def problem(self):
        problem = Problem.get_by_id(self.problem_id)
        if self.secret:
            problem.hide_secret()
        else:
            problem.show_secret()
        if self.contest is not None:
            problem.problem_id = self.contest.get_problem_id_in_contest(problem)
            problem.show('problem_id')

        return problem

    @classmethod
    def create(cls, **kwargs):
        kwargs.setdefault('submit_time', datetime.datetime.now())
        return super().create(**kwargs)

    @staticmethod
    def get_submission_num(user, problem, contest=None):
        if user.is_anonymous:
            return 0
        query = {
            'username': user.username,
            'problem_id': problem.id
        }
        if contest is not None:
            query['contest_id'] = contest.id
        return Submission.search(**query)['meta']['count']

    @staticmethod
    def is_accepted(user, problem, contest):
        if user.is_anonymous:
            return False
        query = {
            'username': user.username,
            'problem_id': problem.id,
            'result': JudgeResult.AC
        }
        if contest is not None:
            query['contest_id'] = contest.id
        return Submission.search(**query)['meta']['count'] > 0
