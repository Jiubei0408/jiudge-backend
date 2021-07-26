from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, orm
from app.models.base import Base
from app.libs.enumerate import ContestType, ContestState


class Contest(Base):
    __tablename__ = 'contest'

    fields = ['id', 'contest_name', 'contest_type', 'start_time', 'end_time', 'state', 'ready']

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_name = Column(String(200), nullable=False)
    contest_type = Column(Enum(ContestType), nullable=False, default=ContestType.ACM)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    ready = Column(Boolean, nullable=False, default=False)

    @classmethod
    def create(cls, **kwargs):
        r = super().create(**kwargs)
        from app.models.scoreboard import Scoreboard
        Scoreboard.create(contest_id=r.id)
        return r

    @orm.reconstructor
    def __init__(self):
        self.secret = True

    def show_secret(self):
        self.secret = False

    def hide_secret(self):
        self.secret = True

    @property
    def state(self):
        from datetime import datetime
        current_time = datetime.now()
        if current_time < self.start_time:
            return ContestState.BEFORE_START
        if self.end_time is not None and current_time > self.end_time:
            return ContestState.ENDED
        return ContestState.RUNNING

    @property
    def users(self):
        from app.models.relationship.user_contest import UserContestRel
        return UserContestRel.get_users_by_contest_id(self.id)

    def is_registered(self, user):
        from app.models.relationship.user_contest import UserContestRel
        return UserContestRel.search(username=user.username, contest_id=self.id)['meta']['count'] > 0

    @property
    def problems(self):
        from app.models.relationship.problem_contest import ProblemContestRel
        problem_list = ProblemContestRel.get_problems_by_contest_id(self.id)
        for problem in problem_list:
            if self.secret:
                problem.hide_secret()
            else:
                problem.show_secret()
        return problem_list

    def get_problem_id_in_contest(self, problem):
        from app.models.relationship.problem_contest import ProblemContestRel
        return ProblemContestRel.search(problem_id=problem.id, contest_id=self.id)['data'][0].problem_id_in_contest

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
        Scoreboard.get_by_contest_id(self.id).delete()
        ProblemContestRel.delete_contest(self.id)
        UserContestRel.delete_contest(self.id)
        RemoteContest.get_by_contest_id(self.id).delete()
        super(Contest, self).delete()
