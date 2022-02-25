from wtforms import StringField
from wtforms.validators import DataRequired

from app.validators.base import BaseForm


class ModifyPasswordForm(BaseForm):
    old_password = StringField(validators=[DataRequired(message='Old password cannot be empty')])
    new_password = StringField(validators=[DataRequired(message='New password cannot be empty')])
