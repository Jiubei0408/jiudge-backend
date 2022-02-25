from flask_login import current_user, login_required
from app.libs.red_print import RedPrint
from app.models.user import User
from app.validators.user import ModifyPasswordForm
from app.libs.error_code import AuthFailed, Success

api = RedPrint('user')


@api.route('/modify_password', methods=['POST'])
@login_required
def modify_password_api():
    form = ModifyPasswordForm().validate_for_api().data_
    if not current_user.check_password(form['old_password']):
        raise AuthFailed('old password isn\'t correct')
    current_user.modify(password=form['new_password'])
    return Success('password has been changed')
