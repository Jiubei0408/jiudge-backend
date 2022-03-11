import math
import time

from app.libs.quest_queue import *
from app.libs.scheduler import *

SCOREBOARD_CALCLATING_FLAG = 'JIUDGE:SCOREBOARD:CALCULATING'


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


def get_contest_problems_summary(contest_id, username):
    from app.models.base import db
    from app.models.problem import Problem
    from app.models.relationship.problem_contest import ProblemContestRel
    from sqlalchemy import exists, and_, func, asc
    from app.models.relationship.user_contest import UserContestRel
    from app.models.submission import Submission
    from app.models.ignorable_results import IgnorableResults
    from app.models.acceptable_results import AcceptableResults
    q_solved = exists().where(
        and_(
            Submission.username == username,
            Submission.contest_id == contest_id,
            Submission.result.in_(AcceptableResults.all()),
            Submission.problem_id == Problem.id
        )
    )
    q_tried = exists().where(
        and_(
            Submission.username == username,
            Submission.contest_id == contest_id,
            Submission.problem_id == Problem.id,
            Submission.result.not_in(IgnorableResults.all())
        )
    )
    q_solve_cnt = db.session.query(func.count()).filter(
        Submission.contest_id == contest_id,
        Submission.result.in_(AcceptableResults.all()),
        Submission.problem_id == Problem.id,
        exists().where(
            and_(
                Submission.username == UserContestRel.username,
                Submission.contest_id == UserContestRel.contest_id
            ))
    ).scalar_subquery()
    q_tried_cnt = db.session.query(func.count()).filter(
        Submission.contest_id == contest_id,
        Submission.result.not_in(IgnorableResults.all()),
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
        order_by(asc(ProblemContestRel.problem_id_in_contest)).all()

    def modify_problem(p, id_, solved, tried, solve_cnt, tried_cnt):
        p.problem_id = id_
        p.solved = solved
        p.tried = tried
        p.solve_cnt = solve_cnt
        p.tried_cnt = tried_cnt
        p.show('problem_id', 'solved', 'tried', 'solve_cnt', 'tried_cnt')
        return p

    return [modify_problem(*info) for info in problem_info_list]


def calc_scoreboard(contest, page=1, page_size=-1):
    from app.models.relationship.problem_contest import ProblemContestRel
    from app.libs.enumerate import ContestRegisterType
    from app.models.base import db
    from app.models.user import User
    problems = ProblemContestRel.get_problems_by_contest_id(contest.id)
    data = {
        'problems': problems,
        'scoreboard': []
    }
    start = page_size * (page - 1)
    user_data = db.session.execute(f'''
        select username, ac_cnt, penalty
        from contest_statistics
        where contest_id = {contest.id}
        order by ac_cnt desc, penalty
        {f'limit {start}, {page_size}' if page_size != -1 else ''};
    ''').fetchall()
    username_list = [row[0] for row in user_data]
    username_list_sql = ', '.join([f'\'{username}\'' for username in username_list])
    first_blood_data = db.session.execute(f'''
        select problem_id, username
        from first_blood
        where contest_id = {contest.id}
    ''').fetchall()
    ac_data = db.session.execute(f'''
        select username, problem_id, penalty
        from penalty_for_accepted_submission
        where contest_id = {contest.id}
        and username in ({username_list_sql})
    ''').fetchall()
    ac_data = {(row[0], row[1]): row[2] for row in ac_data}
    attempt_data = db.session.execute(f'''
        select username, problem_id, attempt_cnt
        from before_accept_cnt_view
        where contest_id = {contest.id}
        and username in ({username_list_sql})
    ''')
    attempt_data = {(row[0], row[1]): row[2] for row in attempt_data}
    first_blood_dict = {}
    for data_row in first_blood_data:
        first_blood_dict[data_row[0]] = data_row[1]
    first_blood = {}
    type_data = db.session.execute(f'''
        select username, type
        from jiudge.user_contest_rel
        where contest_id = {contest.id}
        and username in ({username_list_sql})
    ''')
    type_data = {
        row[0]: row[1]
        for row in type_data
    }
    users = User.search_all(username=username_list)['data']
    users = {
        user.username: user
        for user in users
    }
    for data_row in user_data:
        username, solved, penalty = data_row
        penalty = int(penalty)
        user = users[username]
        register_type = type_data[username]
        row = {
            'solved': solved,
            'penalty': penalty,
            'user': user,
            'register_type': register_type
        }
        for problem in problems:
            pid = problem.problem_id
            cell = {
                'tried': 0,
                'solved': False,
                'solve_time': 0,
                'penalty': 0,
                'first_blood': False
            }
            if (username, problem.id) in ac_data:
                cell['solved'] = True
                cell['solve_time'] = ac_data[(username, problem.id)]
                cell['tried'] = 1
                cell['penalty'] = cell['solve_time']
            if (username, problem.id) in attempt_data:
                cell['tried'] += attempt_data[(username, problem.id)]
                cell['penalty'] += cell['tried'] * 20
            row[pid] = cell
            if problem.id in first_blood_dict and user.username == first_blood_dict[problem.id]:
                first_blood[pid] = cell
                cell['first_blood'] = True
        data['scoreboard'].append(row)
    for i, j in first_blood.items():
        j['first_blood'] = True
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
    return data


def calc_board_for_contest(contest):
    from flask_app import app
    from flask import json
    app.app_context().push()
    redis.sadd(SCOREBOARD_CALCLATING_FLAG, contest.id)
    try:
        data = calc_scoreboard(contest)
        now = datetime.datetime.now()
        from app.models.scoreboard import Scoreboard
        Scoreboard.get_by_contest_id(contest.id).modify(scoreboard_json=json.dumps(data), update_time=now)
    finally:
        redis.srem(SCOREBOARD_CALCLATING_FLAG, contest.id)


def get_scoreboard(contest):
    from app.models.scoreboard import Scoreboard
    from app.config.settings import ScoreboardCacheRefreshSeconds
    from app.libs.enumerate import ContestState
    from app.libs.myredis import redis
    board = Scoreboard.get_by_contest_id(contest.id)
    current_data = json.loads(board.scoreboard_json)
    last_refresh_time = board.update_time
    if last_refresh_time is None:
        from threading import Thread
        Thread(target=calc_board_for_contest, args=(contest,)).start()
        return current_data
    seconds_passed = (datetime.datetime.now() - last_refresh_time).total_seconds()
    if redis.sismember(SCOREBOARD_CALCLATING_FLAG, contest.id):
        return current_data
    if (
            seconds_passed < ScoreboardCacheRefreshSeconds.CONTEST or
            (
                    contest.state != ContestState.RUNNING
                    and last_refresh_time >= contest.end_time
            )
    ) and board.scoreboard_json != '':
        return current_data
    from threading import Thread
    Thread(target=calc_board_for_contest, args=(contest,)).start()
    return current_data
