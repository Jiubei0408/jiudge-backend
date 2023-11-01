from flask_app import app
from app.models.user import User
from app.libs.enumerate import UserPermission


def create_teams(prefix, cnt):  # 创建 cnt 个 prefix 的账号
    import random
    import string
    cnt_len = len(str(cnt))
    all_data = []
    for i in range(1, cnt + 1):
        print("Creating:", i)
        teamname = prefix + str(i).rjust(cnt_len, '0')
        data = {
            'username': teamname,
            'password': ''.join(random.sample(string.ascii_letters + string.digits, 6)),
            'nickname': teamname,
            'permission': UserPermission.NORMAL
        }
        all_data.append(data)
        User.create(**data)
    with open("out.csv", "w") as f:
        f.write('\n'.join([f'{data["username"]}, {data["password"]}' for data in all_data]))


def create_users():  # 创建用户, 用户名为学号, 若用户已经存在, 则将密码修改为学号
    users = open('users.txt', encoding='utf-8').readlines()
    # user.txt 文件中格式为一行两个字符串 username(学号) 和 nickname(姓名), 并用一个空格分隔
    # print(users)
    for user in users:
        user = user.replace('\n', '')
        username, nickname = user.split(' ')
        print("Creating:", username, nickname)
        f = User.get_by_id(username)
        if f is not None:
            f.modify(password=username)
        else:
            data = {
                'username': username,
                'password': username,
                'nickname': nickname,
                'permission': UserPermission.NORMAL
            }
            User.create(**data)


if __name__ == '__main__':
    app.app_context().push()
    create_users()
    # create_teams('team', 10)
