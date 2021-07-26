# 定义数据库信息
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:711010@localhost:3306/jiudge?charset=utf8mb4'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 定义flask信息
SECRET_KEY = 'jiudge'
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True

# 定义redis信息
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'jiubei'
