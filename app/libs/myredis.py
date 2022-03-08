import redis as Redis

from app.config.secure import REDIS_PASSWORD, REDIS_HOST, REDIS_PORT

redis = Redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
