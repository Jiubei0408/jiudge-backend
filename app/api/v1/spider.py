import base64

from app.libs.red_print import RedPrint
from app.validators.spider import SpiderBaseForm
from app.models.quest import Quest
from app.models.problem import Problem
from app.models.relationship.problem_contest import ProblemContestRel
from app.models.contest import Contest
from app.libs.enumerate import QuestStatus
from app.libs.tools import save_to_file

api = RedPrint('spider')


@api.route('/failed', methods=['POST'])
def failed_api():
    form = SpiderBaseForm().validate_for_api().data_
    data = form['data']
    Quest.get_by_id(form['quest_id']).modify(status=QuestStatus.FAILED, message=data['message'])
    return 'ok'


@api.route('/contest_meta/<int:cid>', methods=['POST'])
def update_contest_meta_api(cid):
    """
    :param cid: contest_id
    :param problem_list: 题目列表
    每道题:
    'problem_list': {
        'problem_name': '123', # 题目名
        'remote_problem_id': '1', # 题目id
        'remote_problem_url': 'http://balabala', # 题目链接（可为空）
        'problem_text': '题面文本', # 题面文本（可为空）
        'problem_text_url': 'http://balabala', # 题面链接（可为空）
        'problem_text_file': '',
        'time_limit': 1.5, # 时间限制，单位秒（可为空）
        'space_limit': 1024, # 空间限制，单位KB（可为空）
    },
    'oj_id': '1'
    """
    form = SpiderBaseForm().validate_for_api().data_
    quest_id = form['quest_id']
    data = form['data']
    oj_id = data['oj_id']
    problem_list = data['problem_list']
    contest = Contest.get_by_id(cid)
    if contest is None:
        Quest.get_by_id(quest_id).modify(status=QuestStatus.FINISHED)
        return 'ok'
    try:
        from app.libs.tools import next_problem_id
        cur = 'A'
        for problem in problem_list:
            problem.setdefault('remote_problem_url', '')
            problem.setdefault('problem_text', '')
            problem.setdefault('problem_text_url', '')
            problem.setdefault('time_limit', 0)
            problem.setdefault('space_limit', 0)
            problem.setdefault('oj_id', oj_id)
            problem.setdefault('allowed_lang', [])
            problem_text_file = problem['problem_text_file']
            problem.pop('problem_text_file')
            p = Problem.create(**problem)
            ProblemContestRel.create(problem_id=p.id, contest_id=cid, problem_id_in_contest=cur)
            if problem_text_file != '':
                filename = f'{p.id}.pdf'
                loc = save_to_file(base64.b64decode(problem_text_file), filename, '/problems')
                p.modify(problem_text_file=loc)
            cur = next_problem_id(cur)
        quest = Quest.get_by_id(quest_id)
        quest.modify(status=QuestStatus.FINISHED)
        contest.modify(ready=True)
    except Exception as e:
        print(e)
        print(f'quest {quest_id} error')
    return 'ok'


@api.route('/judge_result/<int:sid>', methods=['POST'])
def update_judge_result_api(sid):
    """
    {
        'result': 'AC',
        'remote_result': 'accepted',
        'time_used': -1,
        'memory_used': -1,
        'compile_info': 'balabala'
    }
    """
    data = SpiderBaseForm().validate_for_api().data_['data']
    from app.models.submission import Submission
    submission = Submission.get_by_id(sid)
    submission.modify(**data)
    submission.quest.modify(status=QuestStatus.FINISHED)
    return 'ok'
