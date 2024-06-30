import time
from typing import Any, Callable, Dict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RequestJSON:
    def __init__(self, **data: Dict[str, Any]):
        self.data = data

    def json(self) -> str:
        return str(
            self.data
        )  # Simplified for demonstration, use actual JSON serialization in practice


class ContentTypeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        content_type = request.headers.get("Content-Type", "").split(";")[
            0
        ]  # Handle content type with charset
        if content_type == "application/json":
            item = RequestJSON(**await request.json())
        elif content_type == "multipart/form-data":
            item = RequestJSON(**await request.form())
        elif content_type == "application/x-www-form-urlencoded":
            item = RequestJSON(**await request.form())
        else:
            return Response(status_code=415, content="Unsupported Media Type")

        request.state.item = item
        response = await call_next(request)
        response.body = item.json().encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        return response


# app.add_middleware(ContentTypeMiddleware)
