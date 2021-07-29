class ScoreboardCacheRefreshSeconds:
    TRAINING = 300  # 不限时题集的榜单刷新时间
    CONTEST = 60


from app.libs.enumerate import JudgeResult

UnRatedJudgeResults = [
    JudgeResult.PENDING, JudgeResult.RUNNING,
    JudgeResult.CE, JudgeResult.SpiderError, JudgeResult.PE, JudgeResult.SE
]
