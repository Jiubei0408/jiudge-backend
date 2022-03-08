from flask_login import current_user, login_required

from app.libs.auth import admin_only
from app.libs.enumerate import ContestState
from app.libs.error_code import *
from app.libs.red_print import RedPrint
from app.libs.tools import get_file_response
from app.models.clarification import Clarification
from app.models.contest import Contest
from app.models.relationship.problem_contest import ProblemContestRel
from app.models.submission import Submission
from app.services.contest import *
from app.services.problem import *
from app.validators.base import *
from app.validators.contest import *
from app.validators.problem import *
from app.libs.enumerate import UserPermission

api = RedPrint('contest')


@api.route('/<int:id_>/register', methods=['POST'])
@login_required
def register_contest(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    if contest.is_registered(current_user):
        return Forbidden(msg='你已经注册过了')
    if contest.state == ContestState.ENDED:
        return Forbidden(msg='比赛已结束')
    form = ContestRegisterForm().validate_for_api().data_
    if contest.password is not None and form['password'] != contest.password:
        return Forbidden(msg='密码错误')
    from app.models.relationship.user_contest import UserContestRel
    UserContestRel.create(username=current_user.username, contest_id=id_)
    return Success('注册完成')


@api.route('/<int:id_>', methods=['GET'])
def get_contest_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    contest.registered = contest.is_registered(current_user)
    contest.show('registered')
    contest.show('problems')
    return Success(data=contest)


@api.route('s', methods=['GET'])
def get_contests_api():
    form = SearchForm().validate_for_api().data_
    if current_user.is_anonymous or current_user.permission != UserPermission.ADMIN:
        form['ready'] = True
    data = Contest.search(**form)
    for contest in data['data']:
        contest.registered = contest.is_registered(current_user)
        contest.show('registered')
    return SearchSuccess(data=data)


@api.route('/<int:id_>/problems', methods=['GET'])
def get_contest_problems(id_):
    from app.services.contest import get_contest_problems_summary
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    if contest.is_admin(current_user) or contest.state == ContestState.ENDED:
        return Success(data=get_contest_problems_summary(
            contest_id=id_,
            username=(current_user.username if not current_user.is_anonymous else None)
        ))
    if contest.state == ContestState.BEFORE_START:
        return Forbidden(msg='比赛还未开始')
    if current_user.is_anonymous:
        return LoginFirst()
    if not contest.is_registered(current_user):
        return Forbidden(msg='你没有注册这场比赛')
    return Success(data=get_contest_problems_summary(
        contest_id=id_,
        username=current_user.username
    ))


@api.route('/<int:id_>/scoreboard', methods=['GET'])
def get_scoreboard_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    from app.services.contest import get_scoreboard
    return get_scoreboard(contest)


@api.route('/<int:id_>/clarifications', methods=['GET'])
def get_clarifications_api(id_):
    form = SearchForm().validate_for_api().data_
    if form['page'] is None:
        form['page'] = 1
    if form['page_size'] is None:
        form['page_size'] = 20
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    return SearchSuccess(data=Clarification.search_by_contest_id(
        contest_id=id_,
        page=form['page'],
        page_size=form['page_size']
    ))


@api.route('/<int:cid>/problem_statement/<string:pid>', methods=['GET'])
def get_problem_statement_api(cid, pid):
    contest = Contest.get_by_id(cid)
    if contest is None:
        return NotFound(f'Contest {cid} not found')
    pcrel = ProblemContestRel.get_by_problem_id_in_contest(cid, pid)
    if pcrel is None:
        return NotFound(f'Contest {cid} has no problem called {pid}')
    problem = pcrel.problem
    problem.show('problem_text', 'problem_text_url', 'has_problem_text_file')
    return Success(data=problem)


@api.route('/<int:cid>/problem_text_file/<string:pid>', methods=['GET'])
def get_problem_text_file_api(cid, pid):
    contest = Contest.get_by_id(cid)
    if contest is None:
        return NotFound(f'Contest {cid} not found')
    if not contest.is_admin(current_user):
        if contest.state == ContestState.BEFORE_START:
            return Forbidden('比赛还未开始')
        elif not contest.is_registered(current_user):
            return Forbidden('你没有注册这场比赛')

    pcrel = ProblemContestRel.get_by_problem_id_in_contest(cid, pid)
    if pcrel is None:
        return NotFound(f'Contest {cid} has no problem called {pid}')
    loc = pcrel.problem.problem_text_file
    if loc == '':
        return NotFound('没有找到题面文件')
    return get_file_response(loc)


@api.route('/<int:cid>/submit/<string:pid>', methods=['POST'])
@login_required
def submit_code_api(cid, pid):
    contest = Contest.get_by_id(cid)
    if contest is None:
        return NotFound(f'Contest {cid} not found')
    if not contest.is_admin(current_user) and contest.state != ContestState.RUNNING:
        return Forbidden('比赛不在进行中')
    pcrel = ProblemContestRel.get_by_problem_id_in_contest(cid, pid)
    if pcrel is None:
        return NotFound(f'Contest {cid} has no problem called {pid}')
    form = SubmitCodeForm().validate_for_api().data_
    if contest.is_admin(current_user) or contest.is_registered(current_user):
        submit_problem(current_user, pcrel.problem, form['code'], form['lang'], contest)
        return Success('提交成功')
    else:
        return Forbidden('你没有注册这场比赛')


@api.route('/<int:cid>/status', methods=['GET'])
def get_status_api(cid):
    contest = Contest.get_by_id(cid)
    if contest is None:
        return NotFound(f'Contest {cid} not found')
    form = SearchSubmissionForm().validate_for_api().data_
    query = {
        'contest_id': cid,
        **{k: v for k, v in form.items() if v is not None and v != ''}
    }
    if 'problem_id' in query:
        from app.models.relationship.problem_contest import ProblemContestRel
        pcrel = ProblemContestRel.get_by_problem_id_in_contest(cid, query['problem_id'])
        if pcrel is not None:
            query['problem_id'] = pcrel.problem_id
    admin = contest.is_admin(current_user)
    if not admin and contest.state == ContestState.BEFORE_START:
        return Forbidden(msg='比赛还未开始')
    if not admin and contest.state == ContestState.RUNNING:
        if current_user.is_anonymous:
            return LoginFirst()
        if not contest.is_registered(current_user):
            return Forbidden(msg='你没有注册这场比赛')
        query['username'] = current_user.username
    search_result = Submission.search(**query, order={'id': 'desc'}, enable_fuzzy={'username'})
    return Success(data=search_result)


@api.route('/<int:id_>/scoreboard', methods=['DELETE'])
@admin_only
def delete_scoreboard_cache_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    from app.models.scoreboard import Scoreboard
    board = Scoreboard.get_by_contest_id(contest.id)
    board.modify(scoreboard_json='{}')
    return Success()


@api.route('/create', methods=['POST'])
@admin_only
def create_contest_api():
    return NotAchieved()


@api.route('/create_remote_contest', methods=['POST'])
@admin_only
def create_remote_contest_api():
    form = CreateRemoteContestForm().validate_for_api().data_
    from app.models.oj import OJ
    oj = OJ.get_by_id(form['oj_id'])
    if oj is None:
        return NotFound(msg='没有找到这个oj')
    if oj.status != 1:
        return Forbidden(msg=f'暂不支持{oj.name}')
    password = None if form['password'] == '' else form['password']
    create_remote_contest(
        contest_name=form['contest_name'],
        contest_type=form['contest_type'],
        start_time=form['start_time'],
        end_time=form['end_time'],
        password=password,
        oj=oj,
        remote_contest_id=form['remote_contest_id']
    )
    return Success(msg='比赛已创建')


@api.route('/<int:id_>', methods=['DELETE'])
@admin_only
def delete_contest_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    contest.delete()
    return DeleteSuccess(msg='删除成功')


@api.route('/<int:id_>/admin/problem_status')
def get_problem_status_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    problems = contest.problems
    for problem in problems:
        problem.show('status')
    return SearchSuccess(data={
        'problems': problems
    })
