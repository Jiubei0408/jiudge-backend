def create_teams(prefix, cnt):
    import random
    import string
    from flask_app import app
    app.app_context().push()
    from app.models.user import User
    from app.libs.enumerate import UserPermission
    cnt_len = len(str(cnt))
    for i in range(1, cnt + 1):
        print("Creating:", i)
        teamname = prefix + str(i).rjust(cnt_len, '0')
        data = {
            'username': teamname,
            'password': ''.join(random.sample(string.ascii_letters + string.digits, 6)),
            'nickname': teamname,
            'permission': UserPermission.NORMAL
        }
        User.create(**data)


if __name__ == '__main__':
    create_teams('team', 10)
