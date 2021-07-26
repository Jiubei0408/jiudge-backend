from werkzeug.exceptions import HTTPException

from app import create_app
from app.libs.error import APIException
from app.libs.error_code import ServerError

app = create_app()


@app.errorhandler(Exception)
def framework_error(e):
    if isinstance(e, APIException):
        return e
    if isinstance(e, HTTPException):
        code = e.code
        msg = e.description
        error_code = 1007
        return APIException(msg, code, error_code)
    else:
        # 调试模式
        # log
        if not app.debug:
            print(e)
            return ServerError()
        else:
            raise e


if __name__ == '__main__':
    from app.libs.scheduler import scheduler
    scheduler.start()
    app.run(host="0.0.0.0", port=5000, debug=True)
