import json

from app.libs.enumerate import QuestType
from app.libs.myredis import redis


def send_crawl_contest_info(contest_id, oj_id, oj_name, remote_contest_id):
    send_quest(oj_name, {
        'type': 'crawl_contest_info',
        'contest_id': contest_id,
        'oj_id': oj_id,
        'remote_contest_id': remote_contest_id
    }, QuestType.CrawlRemoteContestMeta, contest_id)


def send_crawl_problem_info(remote_problem_id, oj):
    from app.models.problem import Problem
    problem = Problem.get_by_oj_id_and_remote_id(oj.id, remote_problem_id)
    send_quest(oj.name, {
        'type': 'crawl_problem_info',
        'problem_id': problem.id,
        'remote_problem_id': remote_problem_id
    }, QuestType.CrawlProblemInfo, problem.id)


def send_submit_problem(submission, problem, code, lang, account=None):
    data = {
        'type': 'submit',
        'submission_id': submission.id,
        'remote_problem_id': problem.remote_problem_id,
        'code': code,
        'lang': lang
    }
    if submission.contest.is_remote():
        data['remote_contest_id'] = submission.contest.remote_contest.remote_contest_id
    quest = send_quest(problem.oj.name, data, QuestType.SubmitSolution, submission.id, account)
    submission.modify(quest_id=quest.id)


def send_crawl_remote_scoreboard(scoreboard_id, oj_name, remote_contest_id):
    send_quest(oj_name, {
        'type': 'crawl_remote_scoreboard',
        'scoreboard_id': scoreboard_id,
        'remote_contest_id': remote_contest_id
    }, QuestType.CrawlRemoteScoreBoard)


def send_quest(oj_name, dict_data, type, relation_id=None, account=None):
    from app.models.quest import Quest
    import hashlib
    import time
    data = dict_data.copy()
    now = int(time.time())
    quest = Quest.create(time_stamp=now, type=type, relation_data_id=relation_id)
    token = hashlib.md5(f'{quest.id}{now}'.encode('utf-8')).hexdigest()
    quest.modify(token=token)
    data.update({
        'quest_id': quest.id,
        'token': token
    })
    queue_name = f'quest_queue_{oj_name}'
    if account is not None:
        queue_name += f':{account}'
    redis.rpush(queue_name, json.dumps(data))
    return quest
