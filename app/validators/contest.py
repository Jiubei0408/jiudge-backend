from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, ValidationError

from app.validators.base import BaseForm, NotRequiredDateTimeRange
from app.libs.enumerate import ContestType


class CreateRemoteContestForm(NotRequiredDateTimeRange):
    oj_id = IntegerField(validators=[DataRequired(message='oj_id cannot be empty')])
    remote_contest_id = StringField(validators=[DataRequired(message='remote_contest_id cannot be empty')])
    contest_name = StringField(validators=[DataRequired(message='Contest name cannot be empty')])
    contest_type = StringField()

    def validate_for_contest_type(self, value):
        if self.contest_type.data not in ContestType.__members__:
            raise ValidationError('Contest Type Not Supported')
        self.contest_type.data = ContestType[self.contest_type.data]

    def validate_start_time(self, value):
        super().validate_start_time(value)
        if self.start_time.data is None:
            raise ValidationError('Start time required')
