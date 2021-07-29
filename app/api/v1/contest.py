from app.libs.red_print import RedPrint
from app.libs.error_code import *
from flask_login import current_user, login_required
from app.models.contest import Contest
from app.models.relationship.problem_contest import ProblemContestRel
from app.libs.enumerate import ContestState
from app.libs.auth import admin_only
from app.validators.contest import *
from app.validators.problem import SubmitCodeForm
from app.services.problem import *
from app.services.contest import *
from app.models.submission import Submission
from app.libs.tools import get_file_response

api = RedPrint('contest')


@api.route('/<int:id_>/register', methods=['POST'])
@login_required
def register_contest(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    if contest.is_registered(current_user):
        return Forbidden(msg='你已经注册过了')
    from app.models.relationship.user_contest import UserContestRel
    UserContestRel.create(username=current_user.username, contest_id=id_)
    return Success('注册完成')


@api.route('s', methods=['GET'])
def get_contests_detail_api():
    contests = Contest.search_all(ready=True)['data']
    for contest in contests:
        contest.registered = contest.is_registered(current_user)
        contest.show('registered')
    return Success(data=contests, dataname='contests')


@api.route('/<int:id_>/problems', methods=['GET'])
def get_contest_problems(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    if contest.is_admin(current_user) or contest.state == ContestState.ENDED:
        contest.show_secret()
        return Success(data=contest.problems)
    if contest.state == ContestState.BEFORE_START:
        return AuthFailed(msg='比赛还未开始')
    if current_user.is_anonymous:
        return AuthFailed(msg='请先登录')
    if not contest.is_registered(current_user):
        return AuthFailed(msg='你没有注册这场比赛')
    contest.hide_secret()
    return Success(data=contest.problems)


@api.route('/<int:id_>/scoreboard', methods=['GET'])
def get_scoreboard_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    from app.services.contest import get_scoreboard
    return get_scoreboard(contest)


@api.route('/<int:id_>/scoreboard', methods=['DELETE'])
@admin_only
def delete_scoreboard_cache_api(id_):
    contest = Contest.get_by_id(id_)
    if contest is None:
        return NotFound(msg='找不到该比赛')
    from app.models.scoreboard import Scoreboard
    board = Scoreboard.get_by_contest_id(contest.id)
    board.modify(scoreboard_json='')
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
    create_remote_contest(
        contest_name=form['contest_name'],
        contest_type=form['contest_type'],
        start_time=form['start_time'],
        end_time=form['end_time'],
        oj=oj,
        remote_contest_id=form['remote_contest_id']
    )
    return Success(msg='比赛已创建')


@api.route('/<int:cid>/problem_text_file/<string:pid>', methods=['GET'])
@login_required
def get_problem_text_file_api(cid, pid):
    contest = Contest.get_by_id(cid)
    if contest is None:
        return NotFound(f'Contest {cid} not found')
    if not contest.is_admin(current_user) and contest.state == ContestState.BEFORE_START:
        return Forbidden('比赛还未开始')
    pcrel = ProblemContestRel.get_problem_by_id_in_contest(cid, pid)
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
    pcrel = ProblemContestRel.get_problem_by_id_in_contest(cid, pid)
    if pcrel is None:
        return NotFound(f'Contest {cid} has no problem called {pid}')
    form = SubmitCodeForm().validate_for_api().data_
    if contest.is_admin(current_user) or contest.is_registered(current_user):
        submit_problem(current_user, pcrel.problem, form['code'], form['lang'], contest)
        return Success('提交成功')
    else:
        return AuthFailed('You should register first')


@api.route('/<int:cid>/status', methods=['GET'])
@login_required
def get_status_api(cid):
    query = {
        'contest_id': cid
    }
    contest = Contest.get_by_id(cid)
    if contest is None:
        return NotFound(f'Contest {cid} not found')
    admin = contest.is_admin(current_user)
    if not admin:
        query['username'] = current_user.username
    submissions = Submission.search_all(**query, order={'submit_time': 'desc'})['data']
    for submission in submissions:
        if admin:
            submission.show_secret()
        else:
            submission.hide_secret()
    return Success(data=submissions, dataname='submissions')


@api.route('/<int:id_>', methods=['DELETE'])
@admin_only
def delete_contest_api(id_):
    Contest.get_by_id(id_).delete()
