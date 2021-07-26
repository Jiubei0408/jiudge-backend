from flask_login import UserMixin
from sqlalchemy import Column, String, Enum

from app import login_manager
from app.libs.error_code import AuthFailed
from app.models.base import Base
from app.libs.enumerate import UserPermission


class User(UserMixin, Base):
    __tablename__ = 'user'
    fields = ['username', 'nickname', 'permission']

    username = Column(String(100), primary_key=True)
    nickname = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    permission = Column(Enum(UserPermission), nullable=False, default=0)

    @property
    def id(self):
        return self.username

    def check_password(self, password):
        return self.password == password

    @staticmethod
    @login_manager.user_loader
    def load_user(id_):
        return User.get_by_id(id_)

    @staticmethod
    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return AuthFailed()
