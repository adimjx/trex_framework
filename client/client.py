import asyncio
import signal
import websockets
import sys

from urllib.parse import urlencode

from client.config import load_config, logger
from client.auth import obtain_jwt, is_token_expired
from client.comms import client_rmq_manager
from client.utils import get_system_uuid, interruptible_sleep

config = load_config()

# Agent runtime flag
"""
boolean flags arent always reliably noticed across all the await calls,
especially under heavy async flow or due to how variable access is optimized in the interpreter.

use asyncio.Event instead of a raw bool.
"""
running_event = asyncio.Event()
running_event.set()

# Shutdown signal handler
def handle_shutdown(signum, frame):
    """
    Signal handler to gracefully shut down the agent process.
    """
    sys.stdout.write("\n")        # move to next line
    sys.stdout.write("\033[F")    # move cursor up one line
    sys.stdout.write("\033[K")    # clear the line
    logger.info("client: received shutdown signal, shutting down gracefully...")
    running_event.clear()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# main agent loop
async def agent():
    global config
    SERVER_IP = config.get("SERVER_IP")
    SERVER_PORT = config.get("SERVER_PORT")
    ORG = config.get("ORG")
    PASSWORD = config.get("PASSWORD")
    MAX_RETRIES = config.get("MAX_RETRIES")
    BACKOFF_FACTOR = config.get("BACKOFF_FACTOR")
    MAX_BACKOFF_TIME = config.get("MAX_BACKOFF_TIME")

    if not SERVER_IP:
        logger.error("client: missing [red]SERVER_IP[/] in config!")
        return

    system_uuid = get_system_uuid()
    if not system_uuid:
        logger.error("client: [red]system UUID[/] not found!")
        return
    
    retry_attempts = 0
    rabbit_connection = None

    logger.debug("client: agent loop initializing.")
    while running_event.is_set():
        try:
            token = await obtain_jwt(running_event, system_uuid, PASSWORD, MAX_RETRIES, BACKOFF_FACTOR, MAX_BACKOFF_TIME)
            if not token:
                logger.error("client: failed to authenticate.")
                return
            params = urlencode({"token": token, "org": ORG})
            ws_url = f"ws://{SERVER_IP}:{SERVER_PORT}/auth/ws/{system_uuid}?{params}"
            # logger.debug(f"client: formatted ws url: {ws_url}")

            # intializing ws connection
            async with websockets.connect(ws_url) as ws:
                logger.info("client: websocket connected.")
                try:
                    retry_attempts = 0  # Reset retry attempts after a successful connection
                    
                    # Connect to RabbitMQ
                    await client_rmq_manager.connect_to_rabbit(system_uuid)
                    # Get queues
                    # action_queue = client_rmq_manager.get_queue("action")
                    # telemetry_queue = client_rmq_manager.get_queue("proc_telemetry")
                    
                    # agent main loop
                    while running_event.is_set():
                        # prevent stale token scenario by refreshing tokens once in a while
                        if is_token_expired(token):
                            token = await obtain_jwt(running_event, system_uuid, PASSWORD, MAX_RETRIES, BACKOFF_FACTOR, MAX_BACKOFF_TIME)
                            logger.debug("client: token refreshed!")
                            if not token:
                                logger.error("client: failed to refresh token.")
                                return

                        # You can send or receive data from the WebSocket server if needed
                        # Example: await websocket.send("Some data")
                        # Or some form of inbound message handling
                        # msg = await ws.recv()
                        # logger.debug(f"Received message: {msg}")
                        if ws.state != websockets.protocol.State.OPEN:
                            logger.warning("client: webSocket connection closed.")
                            break
                        
                        # Sleep for 5 seconds before the next operation
                        await interruptible_sleep(running_event, 5)

                except Exception as e:
                    logger.error(f"client: {e}")

        except Exception as e:
            logger.error("client: looks like some services are down! ☠️")
            if str(e):
                logger.error(f"{e}")
            retry_attempts += 1
            wait_time = min(BACKOFF_FACTOR ** retry_attempts, MAX_BACKOFF_TIME)  # Exponential backoff, capped
            logger.info(f"client: retrying WebSocket connection in {wait_time} seconds...")
            await interruptible_sleep(running_event, wait_time)

    if not running_event.is_set():
        logger.info("client: graceful shutdown target reached...")

if __name__ == "__main__":
    asyncio.run(agent())