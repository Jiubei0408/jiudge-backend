from flask_login import UserMixin
from sqlalchemy import Column, String, Enum
from werkzeug.security import check_password_hash, generate_password_hash

from app import login_manager
from app.libs.enumerate import UserPermission
from app.libs.error_code import LoginFirst
from app.models.base import Base


class User(UserMixin, Base):
    __tablename__ = 'user'
    fields = ['username', 'nickname', 'permission']

    username = Column(String(100), primary_key=True)
    nickname = Column(String(100), nullable=False)
    password_ = Column('password', String(200), nullable=False)
    permission = Column(Enum(UserPermission), nullable=False, default=UserPermission.NORMAL)

    @property
    def id(self):
        return self.username

    @staticmethod
    @login_manager.user_loader
    def load_user(id_):
        return User.get_by_id(id_)

    @staticmethod
    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return LoginFirst()

    def check_password(self, raw):
        if not self.password_ or not raw:
            return False
        return check_password_hash(self.password_, raw)

    @property
    def password(self):
        return self.password_

    @password.setter
    def password(self, raw):
        self.password_ = generate_password_hash(raw)
