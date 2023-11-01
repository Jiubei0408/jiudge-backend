import time


def rejudge(cid):
    """
    重测对应 cid 比赛中的所有 spe
    cid 为对应比赛的 id
    """
    from flask_app import app
    app.app_context().push()
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    from app.libs.quest_queue import send_submit_problem
    submissions = Submission.search_all(result=JudgeResult.SpiderError, contest_id=cid)['data']

    print(len(submissions))
    for submission in submissions:
        print(submission.id)
        time.sleep(5)
        send_submit_problem(submission, submission.problem, submission.code,
                            submission.lang)


def export_submission(cid):
    """
    导出对应 cid 比赛中的所有AC提交
    cid 为对应比赛的 id
    需要在scripts下创建data文件夹
    """
    from flask_app import app
    app.app_context().push()
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    submissions = Submission.search_all(result=JudgeResult.AC, contest_id=cid)['data']
    print(len(submissions))
    for submission in submissions:
        path = 'scripts/data/' + str(submission.id) + "_" + str(submission.username) + ".txt"
        print(path)
        with open(path, "w") as f:
            f.write(submission.code)


def ban(username, cid):
    """
    将 cid 比赛中 username 的提交变成数据删除
    注意该操作不可逆
    """
    from flask_app import app
    app.app_context().push()
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    submissions = Submission.search_all(contest_id=cid, username=username)['data']
    print(len(submissions))
    for submission in submissions:
        submission.modify(result=JudgeResult.UNKNOWN, remote_result='Banned')


if __name__ == '__main__':
    # export_submission(138)
    # ban('31801350', 136)
    rejudge(136)
