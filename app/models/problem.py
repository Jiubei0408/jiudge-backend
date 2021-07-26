import json

from sqlalchemy import Column, Integer, String, ForeignKey, UnicodeText, Float

from app.models.base import Base
from app.models.oj import OJ


class Problem(Base):
    __tablename__ = 'problem'
    fields = ['id', 'problem_name', 'oj', 'remote_problem_id',
              'remote_problem_url', 'problem_text', 'problem_text_url',
              'has_problem_text_file', 'time_limit', 'space_limit',
              'allowed_lang']

    def __init__(self):
        super(Problem, self).__init__()
        self.hide_secret()

    def show_secret(self):
        self.show('id', 'oj', 'remote_problem_id', 'remote_problem_url')

    def hide_secret(self):
        self.hide('id', 'oj', 'remote_problem_id', 'remote_problem_url')

    id = Column(Integer, primary_key=True, autoincrement=True)
    problem_name = Column(String(100))
    oj_id = Column(Integer, ForeignKey(OJ.id))
    remote_problem_id = Column(String(100))
    remote_problem_url = Column(String(300), default='')
    problem_text = Column(UnicodeText, default='')
    problem_text_url = Column(String(300), default='')
    problem_text_file = Column(String(300), default='')
    time_limit = Column(Float, default=0)
    space_limit = Column(Float, default=0)
    _allowed_lang = Column('allowed_lang', String(100), default='')

    @property
    def has_problem_text_file(self):
        return self.problem_text_file != ''

    @property
    def allowed_lang(self):
        return self._allowed_lang.split(',')

    @allowed_lang.setter
    def allowed_lang(self, val):
        self._allowed_lang = ','.join(val)

    @property
    def oj(self):
        return OJ.get_by_id(self.oj_id)
