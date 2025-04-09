import httpx, jwt, time

from client.config import load_config
from client.config import logger
from client.utils import interruptible_sleep

config = load_config()

async def obtain_jwt(running, system_uuid, password, max_retries=5, backoff_factor=2, max_backoff_time=120):
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
            logger.debug("client: successfully obtained JWT.")
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

def is_token_expired(token: str, buffer_seconds: int = 1) -> bool:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp is None:
            return True
        return time.time() > (exp - buffer_seconds)
    except Exception:
        return True