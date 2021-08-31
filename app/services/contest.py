import datetime
import math

from app.libs.quest_queue import *
from app.libs.scheduler import *


def create_remote_contest(contest_name, contest_type, start_time, end_time, oj, remote_contest_id, password):
    from app.models.contest import Contest
    from app.models.remote_contest import RemoteContest
    contest = Contest.create(contest_name=contest_name, contest_type=contest_type, start_time=start_time,
                             end_time=end_time, password=password)
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


def get_problem_list(contest_id, username, show_secret):
    from app.models.base import db
    from app.models.problem import Problem
    from app.models.relationship.problem_contest import ProblemContestRel
    from sqlalchemy import exists, and_, func
    from app.models.relationship.user_contest import UserContestRel
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    from app.config.settings import UnRatedJudgeResults
    q_solved = exists().where(
        and_(
            Submission.username == username,
            Submission.contest_id == contest_id,
            Submission.result == JudgeResult.AC,
            Submission.problem_id == Problem.id
        )
    )
    q_tried = exists().where(
        and_(
            Submission.username == username,
            Submission.contest_id == contest_id,
            Submission.problem_id == Problem.id,
            Submission.result.not_in(UnRatedJudgeResults)
        )
    )
    q_solve_cnt = db.session.query(func.count()).filter(
        Submission.contest_id == contest_id,
        Submission.result == JudgeResult.AC,
        Submission.problem_id == Problem.id,
        exists().where(
            and_(
                Submission.username == UserContestRel.username,
                Submission.contest_id == UserContestRel.contest_id
            ))
    ).scalar_subquery()
    q_tried_cnt = db.session.query(func.count()).filter(
        Submission.contest_id == contest_id,
        Submission.result.not_in(UnRatedJudgeResults),
        Submission.problem_id == Problem.id,
        exists().where(
            and_(
                Submission.username == UserContestRel.username,
                Submission.contest_id == UserContestRel.contest_id
            ))
    ).scalar_subquery()
    problem_info_list = db.session.query(
        Problem,
        ProblemContestRel.problem_id_in_contest,
        q_solved,
        q_tried,
        q_solve_cnt,
        q_tried_cnt
    ).filter(Problem.id == ProblemContestRel.problem_id). \
        filter(ProblemContestRel.contest_id == contest_id). \
        all()

    def modify_problem(p, id_, solved, tried, solve_cnt, tried_cnt):
        p.problem_id = id_
        p.solved = solved
        p.tried = tried
        p.solve_cnt = solve_cnt
        p.tried_cnt = tried_cnt
        p.show('problem_id', 'solved', 'tried', 'solve_cnt', 'tried_cnt')
        if show_secret:
            p.show_secret()
        else:
            p.hide_secret()
        return p

    return [modify_problem(*info) for info in problem_info_list]


def get_scoreboard_cell(user, problem, contest):
    from app.models.base import db
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    data = {
        'tried': 0,
        'solved': False,
        'solve_time': 0,
        'penalty': 0,
        'first_blood': False
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
        data['solve_time'] = math.floor((solve_time - contest.start_time).total_seconds() / 60.0)
        data['tried'] = db.session.query(Submission).filter(
            Submission.username == user.username,
            Submission.problem_id == problem.id,
            Submission.contest_id == contest.id,
            Submission.submit_time <= solve_time,
            Submission.result.not_in(UnRatedJudgeResults)
        ).count()
        data['penalty'] = (data['tried'] - 1) * 20 + data['solve_time']
    else:
        data['tried'] = db.session.query(Submission).filter(
            Submission.username == user.username,
            Submission.problem_id == problem.id,
            Submission.contest_id == contest.id,
            Submission.result.not_in(UnRatedJudgeResults)
        ).count()
    return data


def get_scoreboard(contest):
    from flask import json
    from app.models.scoreboard import Scoreboard
    from app.config.settings import ScoreboardCacheRefreshSeconds
    from app.libs.enumerate import ContestState
    board = Scoreboard.get_by_contest_id(contest.id)
    last_refresh_time = board.update_time
    seconds_passed = (datetime.datetime.now() - last_refresh_time).total_seconds()
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
    from app.libs.enumerate import ContestRegisterType
    problems = ProblemContestRel.get_problems_by_contest_id(contest.id)
    data = {
        'problems': problems,
        'scoreboard': []
    }
    registered = UserContestRel.get_by_contest_id(contest.id)
    first_blood = {}
    for rel in registered:
        row = {
            'solved': 0,
            'penalty': 0,
            'user': rel.user,
            'register_type': rel.type
        }
        for problem in problems:
            problem.hide_secret()
            pid = problem.problem_id
            cell = get_scoreboard_cell(rel.user, problem, contest)
            row[pid] = cell
            if cell['solved']:
                if pid not in first_blood or first_blood[pid]['solve_time'] > cell['solve_time']:
                    first_blood[pid] = cell
                row['solved'] += 1
                row['penalty'] += cell['penalty']
        data['scoreboard'].append(row)
    for i, j in first_blood.items():
        j['first_blood'] = True
    data['scoreboard'].sort(key=lambda x: (-x['solved'], x['penalty']))
    rank = 0
    cnt = 1
    penalty = 0
    solved = 0
    for row in data['scoreboard']:
        if penalty != row['penalty'] or solved != row['solved']:
            rank = cnt
            penalty = row['penalty']
            solved = row['solved']
        row['rank'] = rank
        if row['register_type'] != ContestRegisterType.Starred:
            cnt += 1
    now = datetime.datetime.now()
    data['update_time'] = now
    board.modify(scoreboard_json=json.dumps(data), update_time=now)
    return data
