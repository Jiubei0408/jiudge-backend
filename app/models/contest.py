from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean

from app.libs.enumerate import ContestType, ContestState
from app.models.base import Base


class Contest(Base):
    __tablename__ = 'contest'

    fields = ['id', 'contest_name', 'contest_type', 'start_time', 'end_time',
              'state', 'ready', 'require_password', 'priority', 'notice']

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_name = Column(String(200), nullable=False)
    contest_type = Column(Enum(ContestType), nullable=False, default=ContestType.ACM)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    ready = Column(Boolean, nullable=False, default=False)
    password = Column(String(100))
    priority = Column(Integer, default=0, nullable=False)
    notice = Column(String(1000), default='')

    @classmethod
    def create(cls, **kwargs):
        r = super().create(**kwargs)
        from app.models.scoreboard import Scoreboard
        Scoreboard.create(contest_id=r.id)
        return r

    @property
    def require_password(self):
        return self.password is not None

    @property
    def state(self):
        from datetime import datetime
        current_time = datetime.now()
        if current_time < self.start_time:
            return ContestState.BEFORE_START
        if self.end_time is not None and current_time > self.end_time:
            return ContestState.ENDED
        return ContestState.RUNNING

    def is_registered(self, user):
        if user.is_anonymous:
            return False
        from app.models.relationship.user_contest import UserContestRel
        return UserContestRel.search(username=user.username, contest_id=self.id)['meta']['count'] > 0

    @property
    def problems(self):
        from app.models.relationship.problem_contest import ProblemContestRel
        problem_list = ProblemContestRel.get_problems_by_contest_id(self.id)
        return problem_list

    def get_problem_id_in_contest(self, problem):
        from app.models.relationship.problem_contest import ProblemContestRel
        return ProblemContestRel.search(problem_id=problem.id, contest_id=self.id)['data'][0].problem_id_in_contest

    def get_max_problem_id(self):
        from app.models.relationship.problem_contest import ProblemContestRel
        rows = ProblemContestRel.search_all(contest_id=self.id)['data']
        if len(rows) == 0:
            return ''
        return max([i.problem_id_in_contest for i in rows])

    def add_problem(self, problem):
        from app.models.relationship.problem_contest import ProblemContestRel
        from app.libs.tools import next_problem_id
        id_in_contest = next_problem_id(self.get_max_problem_id())
        ProblemContestRel.create(problem_id=problem.id, contest_id=self.id, problem_id_in_contest=id_in_contest)

    def is_admin(self, user):
        from app.libs.enumerate import UserPermission
        # todo: add permission to someone
        if user.is_anonymous:
            return False
        return user.permission == UserPermission.ADMIN

    def is_remote(self):
        from app.models.remote_contest import RemoteContest
        return RemoteContest.get_by_contest_id(self.id) is not None

    @property
    def remote_contest(self):
        from app.models.remote_contest import RemoteContest
        return RemoteContest.get_by_contest_id(self.id)

    def delete(self):
        from app.models.scoreboard import Scoreboard
        from app.models.relationship.problem_contest import ProblemContestRel
        from app.models.relationship.user_contest import UserContestRel
        from app.models.remote_contest import RemoteContest
        scoreboard = Scoreboard.get_by_contest_id(self.id)
        if scoreboard is not None:
            scoreboard.delete()
        ProblemContestRel.delete_contest(self.id)
        UserContestRel.delete_contest(self.id)
        remote_contest = RemoteContest.get_by_contest_id(self.id)
        if remote_contest is not None:
            remote_contest.delete()
        super(Contest, self).delete()
