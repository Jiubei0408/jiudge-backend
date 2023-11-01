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


class BanSubmissionForm(BaseForm):
    submission_id = StringField()


class ProblemForm(BaseForm):
    oj_id = IntegerField(validators=[DataRequired('oj_id不能为空')])
    remote_problem_id = StringField(validators=[DataRequired('原题目id不能为空')])

    def validate_oj_id(self, value):
        from app.models.oj import OJ
        oj = OJ.get_by_id(self.oj_id.data)
        if oj is None or oj.status != 1:
            raise ValidationError('该oj不可用')


class CrawlProblemInfoForm(ProblemForm):
    pass


class AddProblemForm(ProblemForm):
    pass
