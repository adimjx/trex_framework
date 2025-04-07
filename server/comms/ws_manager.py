import sys

from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timezone

from server.config import CONFIG, logger

# mongo setup
from server.comms.mongo_manager import mongo_manager_conn

class WSManager:
    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WSManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.active_connections: Dict[str, WebSocket] = {}
            self.initialized = True

    async def connect(self, websocket: WebSocket, system_uuid: str, org: str):
        await websocket.accept()
        self.active_connections[system_uuid] = websocket
        logger.info(f"ws_manager_conn: '{org}' - {system_uuid} connected")
        await self._log_connection(system_uuid, org)

    async def disconnect(self, system_uuid: str):
        websocket = self.active_connections.pop(system_uuid, None)
        if websocket:
            sys.stdout.write("\n")        # move to next line
            sys.stdout.write("\033[F")    # move cursor up one line
            sys.stdout.write("\033[K")    # clear the line
            logger.info(f"ws_manager_conn: {system_uuid} disconnected.")
            await self._log_disconnection(system_uuid)
        else:
            logger.warning(f"ws_manager_conn: no active connection found for {system_uuid}")

    async def receive_data(self, websocket: WebSocket, system_uuid: str):
        try:
            while True:
                message = await websocket.receive_text()
                logger.info(f"ws_manager_conn: received from {system_uuid} -> {message}")
                # Now do something with this message...
                # You could decode JSON, route commands, store stuff, etc.
        except WebSocketDisconnect:
            await self.disconnect(system_uuid)
        except Exception as e:
            logger.error(f"ws_manager_conn: error in receive loop for {system_uuid}: {e}")
            await self.disconnect(system_uuid)

    async def _log_connection(self, system_uuid: str, org: str):
        try:
            connected_at = datetime.now(timezone.utc)
            agent_status_col = mongo_manager_conn.get_db()["agent_status"]
            
            await agent_status_col.update_one(
                {"system_uuid": system_uuid},
                {
                    "$set": {
                        "system_uuid": system_uuid,
                        "org": org,
                        "status": "connected",
                        "connected_at": connected_at
                    },
                    "$setOnInsert": {
                        "last_disconnected": None
                    }
                },
                upsert=True
            )
            logger.debug(f"ws: logged connection for {system_uuid} at {connected_at}.")
        except Exception as e:
            logger.error(f"ws: failed to log connection for {system_uuid}: {e}")

    async def _log_disconnection(self, system_uuid: str):
        try:
            disconnected_at = datetime.now(timezone.utc)
            agent_status_col = mongo_manager_conn.get_db()["agent_status"]

            await agent_status_col.update_one(
                {"system_uuid": system_uuid, "status": "connected"},
                {"$set": {"status": "disconnected", "last_disconnected": disconnected_at}}
            )
            logger.debug(f"ws: logged disconnection for {system_uuid} at {disconnected_at}.")
        except Exception as e:
            logger.error(f"ws: failed to log disconnection: {e}")

# Singleton instance to use app-wide
ws_manager_conn = WSManager()