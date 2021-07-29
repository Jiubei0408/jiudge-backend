from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, ValidationError

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
