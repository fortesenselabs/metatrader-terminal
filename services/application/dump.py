logger.info("API is starting up")
app = FastAPI(title="MetaTrader 5 API Server")

# Add the middleware
app.add_middleware(LoggingMiddleware)

# add the router to the app
# Add the REST router to the FastAPI app
app.include_router(get_rest_router(processor), prefix="/api")

# Add the WebSocket router to the FastAPI app
app.include_router(get_websocket_router(processor), prefix="")

#
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
#
# fastapi dev main.py
# Convert to pub-sub with nats
