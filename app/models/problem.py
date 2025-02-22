from sqlalchemy import Column, Integer, String, ForeignKey, UnicodeText, Float

from app.models.base import Base
from app.models.oj import OJ


class Problem(Base):
    __tablename__ = 'problem'
    fields = ['id', 'oj', 'problem_name', 'time_limit', 'space_limit',
              'allowed_lang']

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
    _allowed_lang = Column('allowed_lang', String(1000), default='')

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

    @property
    def status(self):
        from app.models.quest import Quest
        from app.models.base import db, desc
        from app.libs.enumerate import ProblemStatus, QuestType, QuestStatus
        quest = db.session.query(Quest). \
            filter(Quest.relation_data_id == self.id). \
            filter(Quest.type == QuestType.CrawlProblemInfo). \
            order_by(desc(Quest.time_stamp)).first()
        if quest is None:
            return ProblemStatus.NotReady

        if quest.status == QuestStatus.INQUEUE:
            return ProblemStatus.CrawlQuestCreated
        elif quest.status == QuestStatus.FINISHED:
            return ProblemStatus.Ready
        elif quest.status == QuestStatus.RUNNING:
            return ProblemStatus.Crawling
        return ProblemStatus.NotReady

    @classmethod
    def get_by_oj_id_and_remote_id(cls, oj_id, remote_id):
        r = cls.search(oj_id=oj_id, remote_problem_id=remote_id)['data']
        if r:
            return r[0]
        return Problem.create(oj_id=oj_id, remote_problem_id=remote_id)
