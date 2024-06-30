import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from application.config.logger import AppLogger

logger = AppLogger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log the incoming request
        logger.info(f"Incoming request: {request.method} {request.url}")
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Request body: {await request.body()}")

        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # Log the response
        logger.info(f"Outgoing response: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")

        if isinstance(response, JSONResponse):
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            logger.info(f"Response body: {response_body.decode('utf-8')}")

        return response
