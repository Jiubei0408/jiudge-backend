import time


def main():
    from flask_app import app
    app.app_context().push()
    from app.models.submission import Submission
    from app.libs.enumerate import JudgeResult
    from app.libs.quest_queue import send_submit_problem
    submissions = Submission.search_all(result=JudgeResult.SpiderError, contest_id=84)[
        'data']
    print(len(submissions))
    for submission in submissions:
        print(submission.id)
        time.sleep(5)
        send_submit_problem(submission, submission.problem, submission.code,
                            submission.lang)


if __name__ == '__main__':
    main()
