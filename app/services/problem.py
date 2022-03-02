from app.libs.error_code import ParameterException
from app.libs.quest_queue import *


def submit_problem(user, problem, code, lang, contest=None):
    from app.models.submission import Submission
    contest_id = contest.id if contest is not None else None
    if lang not in problem.allowed_lang:
        raise ParameterException(msg=f'disallowed language: {lang}')
    submission = Submission.create(username=user.username, problem_id=problem.id, code=code, lang=lang,
                                   contest_id=contest_id)
    account = None
    if contest is not None and contest.is_remote():
        from app.models.relationship.user_remote_contest_account import UserRemoteContestAccount
        account = UserRemoteContestAccount.get_limited_account(user.username, contest_id)
    send_submit_problem(submission, problem, code, lang, account)
