# To use, rename this file to secure.py and modify your secure settings

# 定义数据库信息
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@host:3306/jiudge?charset=utf8mb4'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 定义flask信息
SECRET_KEY = ''
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True

# 定义redis信息
REDIS_HOST = ''
REDIS_PORT = 6379
REDIS_PASSWORD = ''
