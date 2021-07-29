import datetime
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
    from app.config.settings import UnRatedJudgeResults
    if first_solve:
        data['solved'] = True
        solve_time = first_solve[0].submit_time
        data['solve_time'] = math.floor((solve_time - contest.start_time).seconds / 60.0)
        data['tried'] = db.session.query(Submission).filter(
            Submission.username == user.username,
            Submission.problem_id == problem.id,
            Submission.contest_id == contest.id,
            Submission.submit_time <= solve_time,
            Submission.result.not_in(UnRatedJudgeResults)
        ).count()
    else:
        data['tried'] = db.session.query(Submission).filter(
            Submission.username == user.username,
            Submission.problem_id == problem.id,
            Submission.contest_id == contest.id,
            Submission.result.not_in(UnRatedJudgeResults)
        ).count()
    data['penalty'] = (data['tried'] - 1) * 20 + data['solve_time']
    return data


def get_scoreboard(contest):
    from flask import json
    from app.models.scoreboard import Scoreboard
    from app.config.settings import ScoreboardCacheRefreshSeconds
    from app.libs.enumerate import ContestState
    board = Scoreboard.get_by_contest_id(contest.id)
    last_refresh_time = board.update_time
    seconds_passed = (datetime.datetime.now() - last_refresh_time).seconds
    if (
            seconds_passed < ScoreboardCacheRefreshSeconds.CONTEST or
            (
                    contest.state != ContestState.RUNNING
                    and last_refresh_time >= contest.end_time
            )
    ) and board.scoreboard_json != '':
        return json.loads(board.scoreboard_json)
    from app.models.relationship.problem_contest import ProblemContestRel
    from app.models.relationship.user_contest import UserContestRel
    problems = ProblemContestRel.get_problems_by_contest_id(contest.id)
    data = {
        'problems': problems,
        'scoreboard': []
    }
    users = UserContestRel.get_users_by_contest_id(contest.id)
    for user in users:
        row = {
            'solved': 0,
            'penalty': 0,
            'user': user
        }
        for problem in problems:
            problem.hide_secret()
            cell = get_scoreboard_cell(user, problem, contest)
            row[problem.problem_id] = cell
            if cell['solved']:
                row['solved'] += 1
                row['penalty'] += cell['penalty']
        data['scoreboard'].append(row)
    data['scoreboard'].sort(key=lambda x: (-x['solved'], x['penalty']))
    now = datetime.datetime.now()
    data['update_time'] = now
    board.modify(scoreboard_json=json.dumps(data), update_time=now)
    return data
