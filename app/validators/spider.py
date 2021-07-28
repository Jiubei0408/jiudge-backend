import json

from app.validators.base import BaseForm
from wtforms import IntegerField, StringField
from wtforms.validators import ValidationError, DataRequired
from app.models.quest import Quest
from app.libs.enumerate import QuestStatus


class SpiderBaseForm(BaseForm):
    quest_id = IntegerField()
    token = StringField()
    data = StringField()

    def validate_token(self, value):
        if self.quest_id.data is None:
            raise ValidationError('quest_id cannot be empty')
        quest = Quest.get_by_id(self.quest_id.data)
        if quest is None:
            raise ValidationError('quest can not found')
        if quest.status == QuestStatus.FINISHED:
            raise ValidationError('quest has been finished')
        if self.token.data != quest.token:
            raise ValidationError('token validate failed')


class SpiderFailedForm(SpiderBaseForm):
    def validate_token(self, value):
        if self.quest_id.data is None:
            raise ValidationError('quest_id cannot be empty')
        quest = Quest.get_by_id(self.quest_id.data)
        if quest is None:
            raise ValidationError('quest can not found')
        if self.token.data != quest.token:
            raise ValidationError('token validate failed')
