import functools

from flask_login import current_user

from app.libs.error_code import AuthFailed
from app.libs.enumerate import UserPermission


def admin_only(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_anonymous or current_user.permission != UserPermission.ADMIN:
            raise AuthFailed(msg='您不是管理员')
        return func(*args, **kwargs)

    return wrapper
