from flask_login import current_user, login_required

from app.libs.error_code import Forbidden, Success
from app.libs.red_print import RedPrint
from app.validators.user import ModifyPasswordForm

api = RedPrint('user')


@api.route('/modify_password', methods=['POST'])
@login_required
def modify_password_api():
    form = ModifyPasswordForm().validate_for_api().data_
    if not current_user.check_password(form['old_password']):
        return Forbidden('old password isn\'t correct')
    current_user.modify(password=form['new_password'])
    return Success('password has been changed')
