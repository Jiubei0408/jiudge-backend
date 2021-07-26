from app.libs.red_print import RedPrint
from app.models.oj import OJ
from app.libs.error_code import SearchSuccess

api = RedPrint('oj')


@api.route('', methods=['GET'])
def get_oj_list_api():
    return SearchSuccess(data=OJ.search_all(status=1))
