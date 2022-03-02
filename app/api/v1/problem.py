from app.libs.auth import admin_only
from app.libs.error_code import *
from app.libs.red_print import RedPrint
from app.validators.problem import CrawlProblemInfoForm

api = RedPrint('problem')


@api.route('/crawl_problem_info', methods=['POST'])
@admin_only
def crawl_problem_api():
    from app.models.oj import OJ
    from app.libs.quest_queue import send_crawl_problem_info
    form = CrawlProblemInfoForm().validate_for_api().data_
    oj = OJ.get_by_id(form['oj_id'])
    if oj is None or oj.status == 0:
        return NotFound('找不到该oj')
    send_crawl_problem_info(form['remote_problem_id'], oj)
    return CreateSuccess('任务已创建')
