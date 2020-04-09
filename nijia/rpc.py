from typing import Dict, Callable, Awaitable, Any, Union, Optional

from .log import logger


class Request:
    def __init__(self, method: str, params: Optional[Dict[str, Any]] = None):
        self.method = method
        self.params = params or {}

    def to_dict(self) -> Dict[str, Any]:
        return {'method': self.method, 'params': self.params}

    def __repr__(self):
        return repr(self.to_dict())

    def __str__(self):
        return str(self.to_dict())


class Response:
    def __init__(self,
                 result: Any = None,
                 error: Optional[Dict[str, Any]] = None):
        self.result = result
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {'result': self.result, 'error': self.error}

    def __repr__(self):
        return repr(self.to_dict())

    def __str__(self):
        return str(self.to_dict())


class ErrorResponse(Response):
    def __init__(self, code: int, message: str = ''):
        super().__init__(error={'code': code, 'message': message})


class ErrorCode:
    NO_SUCH_METHOD = 100
    INVOKE_FAILED = 101
    DATABASE_FAILED = 102


class Service:
    def __init__(self):
        self._methods: Dict[str, Callable[..., Awaitable[Any]]] = {}

    def method(
            self,
            name_or_func: Union[str, Callable[..., Awaitable[Any]]]
    ) -> Any:
        if isinstance(name_or_func, Callable):
            func = name_or_func
            self._methods[func.__name__] = func
            return func
        else:
            def deco(f: Callable) -> Callable:
                name = name_or_func
                self._methods[name] = f
                return f

            return deco

    async def invoke(self, request: Request) -> Response:
        if request.method not in self._methods:
            return ErrorResponse(
                ErrorCode.NO_SUCH_METHOD,
                f'没有 "{request.method}" 这个方法'
            )

        try:
            func = self._methods[request.method]
            res = await func(**request.params)
            if not isinstance(res, Response):
                res = Response(res)
            return res
        except Exception as e:
            logger.exception(e)
            return ErrorResponse(
                ErrorCode.INVOKE_FAILED,
                f'调用 "{request.method}" 时抛出异常'
            )
