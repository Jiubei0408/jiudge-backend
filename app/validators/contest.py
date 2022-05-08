from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, ValidationError

from app.libs.enumerate import ContestType
from app.validators.base import BaseForm, NotRequiredDateTimeRange


class ContestRegisterForm(BaseForm):
    password = StringField()


class CreateContestForm(NotRequiredDateTimeRange):
    contest_name = StringField(validators=[DataRequired(message='Contest name cannot be empty')])
    contest_type = StringField()
    password = StringField()

    def validate_contest_type(self, value):
        if self.contest_type.data not in ContestType.__members__:
            raise ValidationError('Contest Type Not Supported')
        self.contest_type.data = ContestType[self.contest_type.data]

    def validate_start_time(self, value):
        super().validate_start_time(value)
        if self.start_time.data is None:
            raise ValidationError('Start time required')


class ModifyContestForm(NotRequiredDateTimeRange):
    contest_name = StringField(validators=[DataRequired(message='Contest name cannot be empty')])
    contest_type = StringField()
    password = StringField()
    ready = IntegerField()
    priority = IntegerField()

    def validate_contest_type(self, value):
        if self.contest_type.data is None:
            return
        if self.contest_type.data not in ContestType.__members__:
            raise ValidationError('Contest Type Not Supported')
        self.contest_type.data = ContestType[self.contest_type.data]

    def validate_ready(self, value):
        if self.ready.data is None:
            return
        if self.ready.data not in [0, 1]:
            raise ValidationError('ready should be one of [0, 1]')


class CreateRemoteContestForm(NotRequiredDateTimeRange):
    oj_id = IntegerField(validators=[DataRequired(message='oj_id cannot be empty')])
    remote_contest_id = StringField(validators=[DataRequired(message='remote_contest_id cannot be empty')])
    contest_name = StringField(validators=[DataRequired(message='Contest name cannot be empty')])
    contest_type = StringField()
    password = StringField()

    def validate_contest_type(self, value):
        if self.contest_type.data not in ContestType.__members__:
            raise ValidationError('Contest Type Not Supported')
        self.contest_type.data = ContestType[self.contest_type.data]

    def validate_start_time(self, value):
        super().validate_start_time(value)
        if self.start_time.data is None:
            raise ValidationError('Start time required')


class NewClarificationForm(BaseForm):
    to = StringField()
    problem_id = StringField()
    content = StringField(validators=[DataRequired(message='content cannot be empty')])
