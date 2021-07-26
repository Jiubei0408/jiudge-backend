import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.config.secure import SQLALCHEMY_DATABASE_URI

jobstores = {
    'default': SQLAlchemyJobStore(SQLALCHEMY_DATABASE_URI)
}

scheduler = BackgroundScheduler(jobstores=jobstores)


def schedule_datetime(func, time, args):
    if time < datetime.datetime.now():
        func(*args)
        return
    return scheduler.add_job(func, 'date', args, run_date=time)


def schedule_during(func, args, start_time, end_time, seconds):
    func(*args)
    if end_time is None or end_time < datetime.datetime.now():
        return
    return scheduler.add_job(func, 'interval', args=args, start_date=start_time, end_date=end_time, seconds=seconds)
