"""API 全局异常处理器

将业务异常和 Python 标准异常统一转换为 JSON 响应，格式与 ``ApiResponse`` 一致。
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import RagError


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """ValueError → 400 请求参数错误"""
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": str(exc) or "请求参数错误",
            "data": None,
        },
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """HTTPException → 对应状态码"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": str(exc.detail) or "HTTP 错误",
            "data": None,
        },
    )


async def rag_error_handler(request: Request, exc: RagError) -> JSONResponse:
    """RagError → 业务异常码

    将自定义 RagError 中的 code/message/detail 映射为 ``ApiResponse`` 格式。
    状态码统一使用 400（客户端请求导致的业务异常）。
    """
    return JSONResponse(
        status_code=400,
        content={
            "code": 400,
            "message": exc.message,
            "data": None,
        },
    )


async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """未预期的异常 → 500 内部服务器错误"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "内部服务器错误",
            "data": None,
        },
    )


def register_exception_handlers(app) -> None:
    """在 FastAPI app 上注册所有异常处理器"""
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RagError, rag_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
