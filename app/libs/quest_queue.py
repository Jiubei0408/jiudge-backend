import json

import redis as Redis
from app.config.secure import REDIS_PASSWORD, REDIS_HOST, REDIS_PORT
from app.libs.enumerate import QuestType

redis = Redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)


def send_crawl_contest_info(contest_id, oj_id, oj_name, remote_contest_id):
    send_quest(oj_name, {
        'type': 'crawl_contest_info',
        'contest_id': contest_id,
        'oj_id': oj_id,
        'remote_contest_id': remote_contest_id
    }, QuestType.CrawlRemoteContestMeta)


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
