from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from app.validators.base import BaseForm


class SubmitCodeForm(BaseForm):
    code = StringField(validators=[DataRequired('代码不能为空')])
    lang = StringField(validators=[DataRequired('语言不能为空')])


class SearchSubmissionForm(BaseForm):
    username = StringField()
    problem_id = StringField()
    result = StringField()
    page = IntegerField()
    page_size = IntegerField()


class CrawlProblemInfoForm(BaseForm):
    oj_id = IntegerField(validators=[DataRequired('oj_id不能为空')])
    remote_problem_id = StringField(validators=[DataRequired('原题目id不能为空')])
