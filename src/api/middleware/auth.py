"""
API 认证中间件 - 简单 API Key 认证
"""

import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key 认证中间件
    - 白名单路径（健康检查、文档）不需要认证
    - 其他路径需要在 Header 中携带 X-API-Key
    """

    # 不需要认证的路径前缀
    WHITELIST = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    async def dispatch(self, request: Request, call_next):
        # 白名单路径跳过认证
        path = request.url.path
        if any(path == wp or path.startswith(wp + "/") for wp in self.WHITELIST if wp != "/") or path == "/":
            return await call_next(request)

        # 获取 API Key
        api_key = request.headers.get("X-API-Key", "")
        expected_key = os.getenv("API_KEY", "")

        # 如果没有配置 API Key，跳过认证（开发模式）
        if not expected_key:
            return await call_next(request)

        # 验证 API Key
        if api_key != expected_key:
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "message": "无效的 API Key，请在请求头中携带 X-API-Key",
                },
            )

        return await call_next(request)
