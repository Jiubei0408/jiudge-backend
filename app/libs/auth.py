import functools

from flask_login import current_user

from app.libs.enumerate import UserPermission
from app.libs.error_code import Forbidden


def admin_only(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_anonymous or current_user.permission != UserPermission.ADMIN:
            raise Forbidden(msg='您不是管理员')
        return func(*args, **kwargs)

    return wrapper
