import functools
import mimetypes
from io import BytesIO
from urllib.parse import quote

from flask import make_response
from flask_login import current_user, login_required

from app.libs.auth import admin_only
from app.libs.enumerate import ContestState
from app.libs.enumerate import UserPermission
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

api = RedPrint('contest')


def validate_contest(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        id_ = kwargs.pop('id_')
        contest = Contest.get_by_id(id_)
        if contest is None:
            return NotFound(msg='找不到该比赛')
        return func(*args, **kwargs, contest=contest)

    return wrapper


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
    contest.admin = contest.is_admin(current_user)
    contest.show('registered')
    contest.show('problems')
    contest.show('admin')
    return Success(data=contest)


@api.route('s', methods=['GET'])
def get_contests_api():
    form = SearchForm().validate_for_api().data_
    if current_user.is_anonymous or current_user.permission != UserPermission.ADMIN:
        form['ready'] = True
    form['order'] = {'priority': 'desc', 'id': 'desc'}
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


@api.route('/<int:id_>/contestants', methods=['GET'])
@validate_contest
def get_contestants_api(contest):
    from app.models.relationship.user_contest import UserContestRel
    return Success(data=UserContestRel.search_all(contest_id=contest.id)['data'])


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


@api.route('/<int:id_>/new_clar', methods=['POST'])
@validate_contest
@login_required
def new_clar_api(contest):
    from app.models.user import User
    form = NewClarificationForm().validate_for_api().data_
    if form['to'] != 'jury' and not contest.is_admin(current_user):
        return Forbidden(msg='你没有向他发消息的权限')
    if form['to'] == '':
        form['to'] = None
    else:
        to = User.get_by_id(form['to'])
        if to is None:
            return NotFound(msg='找不到该用户')
        form['to'] = to
    if form['problem_id'] == '':
        form['problem_id'] = None
    Clarification.create(who=current_user, contest_id=contest.id, **form)
    return CreateSuccess(msg='已发送')


@api.route('/<int:id_>/clar_count', methods=['GET'])
@validate_contest
@login_required
def get_clar_count_api(contest):
    return Success(data=get_clarification_unread_count(current_user, contest))


@api.route('/read_clar/<int:id_>', methods=['POST'])
@login_required
def read_clar_api(id_):
    from app.models.relationship.user_clar_read import UserClarRead
    clar = Clarification.get_by_id(id_)
    contest = Contest.get_by_id(clar.contest_id)
    if clar.to is None:
        UserClarRead.create(username=current_user.username, clar_id=id_)
    elif contest.is_admin(current_user):
        UserClarRead.create(username=clar.to.username, clar_id=id_)
    else:
        return Forbidden(msg='您不是本场比赛的管理员')
    return Success()


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


@api.route('/<int:id_>/export_scoreboard', methods=['GET', 'POST'])
@admin_only
def export_scoreboard_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    io = BytesIO()
    export_contest_scoreboard(contest, io)
    filename = quote("{}_{}.xlsx".format(contest.contest_name, datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
    file = make_response(io.getvalue())
    io.close()
    mime_type = mimetypes.guess_type('%s.xlsx' % filename)[0]
    file.headers['Content-Type'] = mime_type
    file.headers["Cache-Control"] = "no-cache"
    file.headers['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(filename)
    return file


@api.route('/<int:id_>/scoreboard', methods=['DELETE'])
@admin_only
def delete_scoreboard_cache_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    from app.models.scoreboard import Scoreboard
    board = Scoreboard.get_by_contest_id(contest.id)
    board.modify(scoreboard_json='{}', update_time=None)
    return Success()


@api.route('/create', methods=['POST'])
@admin_only
def create_contest_api():
    form = CreateContestForm().validate_for_api().data_
    Contest.create(**form)
    return CreateSuccess()


@api.route('/admin/<int:id_>', methods=['GET'])
@validate_contest
@admin_only
def get_contest_admin_api(contest):
    contest.show('password')
    return Success(data=contest)


@api.route('/<int:id_>/modify', methods=['POST'])
@validate_contest
@admin_only
def modify_contest_api(contest):
    form = ModifyContestForm().validate_for_api().data_
    if form['ready'] is None:
        form['ready'] = contest.ready
    if form['priority'] is None:
        form['priority'] = contest.priority
    contest.modify(**form)
    return Success('修改成功')


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


@api.route('/<int:id_>/problem_status')
def get_problem_status_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    problems = contest.problems
    for problem in problems:
        problem.show('oj')
        problem.show('remote_problem_id')
        problem.show('status')
    return SearchSuccess(data={
        'problems': problems
    })


@api.route('/<int:id_>/add_problem', methods=['POST'])
@validate_contest
@admin_only
def add_problem_api(contest):
    from app.models.problem import Problem
    form = AddProblemForm().validate_for_api().data_
    problem = Problem.get_by_oj_id_and_remote_id(form['oj_id'], form['remote_problem_id'])
    if problem in contest.problems:
        return ParameterException('题目已经在比赛中了')
    contest.add_problem(problem)
    return CreateSuccess('题目已添加')
