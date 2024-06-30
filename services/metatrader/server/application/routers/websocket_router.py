import json
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from application.config.config import Settings
from application.config.logger import AppLogger
from application.lib.processor import MetaTraderDataProcessor
from application.models.kline_models import WsRequest
from application.models.enum_types import DataMode, TimeFrame
from application.services.kline_service import KlineService

# Create an APIRouter instance
ws_router = APIRouter(tags=["Websocket"])


class WebSocketRouter:
    def __init__(self, logger: AppLogger, processor: MetaTraderDataProcessor):
        self.logger = logger
        self.processor = processor
        self.kline_service = KlineService(logger, processor)
        self.connected_clients: Set[WebSocket] = set()

        # Add routes
        self.add_routes()

    def add_routes(self):
        ws_router.add_api_websocket_route(
            "/ws/kline/{symbol}/{interval}", self.ws_kline
        )
        ws_router.add_api_websocket_route("/ws/tick/{symbol}", self.ws_ticker)
        ws_router.add_api_websocket_route("/ws", self.handle_websocket)

    async def ws_kline(self, websocket: WebSocket, symbol: str, interval: str):
        await websocket.accept()
        try:
            data = await websocket.receive_text()
            self.logger.info(data)
            request = WsRequest(**json.loads(data))

            while True:
                await self.kline_service.add_subscriber(request, symbol, interval)

                # Query for the kline data
                kline_data = await self.kline_service.get_kline_data(symbol, interval)

                await websocket.send_json(kline_data.model_dump())

                # Wait for specified amount of time before sending another data
                time_frame = TimeFrame.from_string(kline_data.kline.interval)
                if time_frame is not None:
                    await asyncio.sleep(time_frame.to_interval().value)

        except WebSocketDisconnect:
            self.logger.info("WebSocket connection closed")

    async def ws_ticker(self, websocket: WebSocket, symbol: str):
        await websocket.accept()

        try:
            data = await websocket.receive_text()
            self.logger.info(data)

            while True:
                # Query for the tick data
                tick_data = await self.kline_service.get_tick_data(symbol)

                await websocket.send_json(tick_data.model_dump())
        except WebSocketDisconnect:
            self.logger.info("WebSocket connection closed")

    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.connected_clients.add(websocket)

        try:
            while True:
                data = await websocket.receive_text()
                # Process received data here (e.g., parse JSON, trigger actions)
                self.logger.info(f"Received: {data}")

                # Using processor for data access
                response_data = self.processor.get_data("", DataMode.TICK)
                self.logger.info(f"response_data: {response_data}")

                # Send a response (if applicable)
                await websocket.send_json(response_data)
        except WebSocketDisconnect:
            self.logger.info("WebSocket connection closed")

        # Remove the client from the connected clients set
        finally:
            self.connected_clients.remove(websocket)
            await websocket.close()


def get_websocket_router(
    logger: AppLogger, processor: MetaTraderDataProcessor
) -> APIRouter:
    WebSocketRouter(logger, processor)
    return ws_router


# Websocket with swagger UI:
# https://stackoverflow.com/questions/63639197/how-to-document-websockets
