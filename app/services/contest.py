import math

from app.libs.quest_queue import *
from app.libs.scheduler import *


def create_remote_contest(contest_name, contest_type, start_time, end_time, oj, remote_contest_id):
    from app.models.contest import Contest
    from app.models.remote_contest import RemoteContest
    contest = Contest.create(contest_name=contest_name, contest_type=contest_type, start_time=start_time,
                             end_time=end_time)
    RemoteContest.create(oj_id=oj.id, remote_contest_id=remote_contest_id, contest_id=contest.id)
    schedule_datetime(task_crawl_contest_info, start_time, (contest.id, oj.id, oj.name, remote_contest_id))


def task_crawl_contest_info(contest_id, oj_id, oj_name, remote_contest_id):
    from flask_app import create_app
    with create_app().app_context():
        send_crawl_contest_info(contest_id, oj_id, oj_name, remote_contest_id)


def create_crawl_remote_scoreboard_schedule(scoreboard_id, remote_contest):
    # todo: 暂时禁用
    return
    schedule_during(
        task_crawl_remote_scoreboard,
        (scoreboard_id, remote_contest.oj.name, remote_contest.remote_contest_id),
        remote_contest.contest.start_time, remote_contest.contest.end_time, 60
    )


def task_crawl_remote_scoreboard(scoreboard_id, oj_name, remote_contest_id):
    from flask_app import create_app
    with create_app().app_context():
        send_crawl_remote_scoreboard(scoreboard_id, oj_name, remote_contest_id)


def get_scoreboard_cell(user, problem, contest):
    from app.models.base import db
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    data = {
        'tried': 0,
        'solved': False,
        'solve_time': 0,
        'penalty': 0
    }
    first_solve = Submission.search(
        username=user.username,
        problem_id=problem.id,
        contest_id=contest.id,
        result=JudgeResult.AC,
        order={'submit_time': 'ASC'})['data']
    if not first_solve:
        data['tried'] = Submission.search(
            username=user.username,
            problem_id=problem.id,
            contest_id=contest.id
        )['meta']['count']
        return data
    data['solved'] = True
    solve_time = first_solve[0].submit_time
    data['solve_time'] = math.ceil((solve_time - contest.start_time).seconds / 60.0)
    data['tried'] = db.session.query(Submission).filter(
        Submission.username == user.username,
        Submission.problem_id == problem.id,
        Submission.contest_id == contest.id,
        Submission.submit_time <= solve_time
    ).count()
    data['penalty'] = (data['tried'] - 1) * 20 + data['solve_time']
    return data
