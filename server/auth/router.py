# server/auth/router.py

"""
Auth logic
-x-x-
Agent authentication endpoints
"""

from fastapi import APIRouter, HTTPException, WebSocket, Query
from pydantic import BaseModel

from .core import *
from server.decorators.json_response import json_response
from server.config import logger
from server.comms import ws_manager_conn

auth_router = APIRouter()

# token request model for client auth.
class TokenRequest(BaseModel):
    system_uuid: str
    password: str

@auth_router.post("/get_token")
@json_response(status_code=200)
async def get_token(token_request: TokenRequest):
    # Access the data using the model
    system_uuid = token_request.system_uuid
    password = token_request.password

    # Validate user credentials
    if not validate_agent_credentials(system_uuid, password):
        logger.debug(f"auth: agent with ID: {system_uuid} tried to acquire a token with invalid credentials")
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create and return the token
    token = create_access_token(data={"system_uuid": system_uuid})
    logger.debug(f"auth: agent with ID: {system_uuid} successfully acquired an access token")
    return {"access_token": token, "token_type": "bearer"}

# WebSocket endpoint
@auth_router.websocket("/ws/{system_uuid}")
async def websocket_endpoint(
    websocket: WebSocket,
    system_uuid: str,
    token: str = Query(...),
    org: str = Query(None)  # <-- grab the org param
):
    # Verify the JWT token & the agent
    payload = verify_access_token(token)
    if payload is None:
        logger.debug(f"auth: agent with ID: {system_uuid} attempted ws with an invalid access token")
        await websocket.close(code=4001)
        return

    if not verify_agent_uuid(system_uuid, payload.get("system_uuid")):
        logger.debug(f"auth: agent with ID: {system_uuid} attempted ws with mismatched credentials")
        await websocket.close(code=4001)
        return

    if not org:
        logger.debug(f"auth: agent with ID: {system_uuid} attempted ws without providing 'org'")
        await websocket.close(code=4002)  # Another custom close code
        return

    logger.debug(f"auth: agent with ID: {system_uuid} attempted ws with a valid access token")
    await ws_manager_conn.connect(websocket, system_uuid, org)
    await ws_manager_conn.receive_data(websocket, system_uuid)