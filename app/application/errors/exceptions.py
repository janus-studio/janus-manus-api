from typing import Any

from anyio import ClosedResourceError


class AppException(RuntimeError):
    def __init__(
            self,
            code: int = 400,
            status_code: int = 400,
            msg: str = '应用发生错误请稍后重试',
            data: Any = None,
    ):
        self.code = code
        self.status_code = status_code
        self.msg = msg
        self.data = data
        super().__init__()


class BadRequestError(AppException):
    def __init__(self, msg: str = '客户端请求参数错误，请检查后重试。'):
        super().__init__(code=400, status_code=400, msg=msg)


class NotFoundError(AppException):
    def __init__(self, msg: str = '请求的资源不存在，请检查后重试。'):
        super().__init__(code=404, status_code=404, msg=msg)


class ValidationError(AppException):
    def __init__(self, msg: str = '客户端请求参数校验失败，请检查后重试。'):
        super().__init__(code=422, status_code=422, msg=msg)


class TooManyRequestsError(AppException):
    def __init__(self, msg: str = '请求频率过快，请稍后重试。'):
        super().__init__(code=429, status_code=429, msg=msg)


class ServerRequestError(AppException):
    def __init__(self, msg: str = '服务器出现异常，请稍后重试。'):
        super().__init__(code=500, status_code=500, msg=msg)
