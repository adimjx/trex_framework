import asyncio
import httpx
import signal
import websockets
import sys

from urllib.parse import urlencode
from websockets.exceptions import ConnectionClosed

from client.config import load_config
from client.config import logger
from client.utils import get_system_uuid

config = load_config()

# Agent runtime flag
running = True

# Shutdown signal handler
def handle_shutdown(signum, frame):
    """
    Signal handler to gracefully shut down the agent process.
    """
    global running
    sys.stdout.write("\n")        # move to next line
    sys.stdout.write("\033[F")    # move cursor up one line
    sys.stdout.write("\033[K")    # clear the line
    logger.info("client: received shutdown signal, shutting down gracefully...")
    running = False

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

async def interruptible_sleep(duration):
    """
    Custom sleep that checks for shutdown signal and interrupts if necessary.
    """
    step = 1  # Sleep in 1-second intervals
    for _ in range(duration):
        if not running:
            break  # Stop sleeping if shutdown signal received
        await asyncio.sleep(step)

async def obtain_jwt(system_uuid, password, max_retries=5, backoff_factor=2, max_backoff_time=120):
    url = f"http://{config['SERVER_IP']}:{config['SERVER_PORT']}/auth/get_token"
    retry_attempts = 0

    while retry_attempts < max_retries:
        if not running:
            logger.info("client: shutdown triggered during auth. routine...")
            return None

        try:
            logger.debug(f"client: sending request to obtain JWT at {url}")
            payload = {"system_uuid": system_uuid, "password": password}

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)

            # logger.debug(f"client: raw response: {response.status_code} - {response.text}")
            response.raise_for_status()

            token_data = response.json()
            # logger.debug(f"client: parsed token data: {token_data}")
            token = token_data["data"]["access_token"]
            logger.info("client: successfully obtained JWT.")
            return token

        except httpx.HTTPError as e:
            logger.exception("client: HTTP error occurred during token acquisition... is the server up?", exc_info=False)
        except Exception as e:
            logger.exception("client: unexpected error during token acquisition.")

        retry_attempts += 1
        wait_time = min(backoff_factor ** retry_attempts, max_backoff_time)
        logger.info(f"client: retrying auth. in {wait_time} seconds...")
        await interruptible_sleep(wait_time)

    logger.error("client: failed to authenticate despite multiple attempts.")
    return None

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

    logger.debug("client: agent loop initializing")
    while running:
        try:
            token = await obtain_jwt(system_uuid, PASSWORD)
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
                    
                    # agent main loop
                    while running:
                        # You can send or receive data from the WebSocket server if needed
                        # Example: await websocket.send("Some data")
                        # Or some form of inbound message handling
                        # msg = await ws.recv()
                        # logger.debug(f"Received message: {msg}")
                        if ws.state != websockets.protocol.State.OPEN:
                            logger.warning("client: webSocket connection closed.")
                            break
                        
                        # Sleep for 5 seconds before the next operation
                        await interruptible_sleep(5)

                except Exception as e:
                    logger.error(f"some error: {e}")

        except Exception as e:
            logger.error("client: looks like the server &/ rabbit is down ☠️")
            if str(e):
                logger.error(f"{e}")
            retry_attempts += 1
            wait_time = min(BACKOFF_FACTOR ** retry_attempts, MAX_BACKOFF_TIME)  # Exponential backoff, capped
            logger.info(f"client: retrying WebSocket connection in {wait_time} seconds...")
            await interruptible_sleep(wait_time)

    if not running:
        logger.info("client: graceful shutdown target reached...")

if __name__ == "__main__":
    asyncio.run(agent())