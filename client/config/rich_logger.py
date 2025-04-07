# server/config/rich_logger.py

"""
Rich logger configuration
-x-x-
A custom logger configuration for functionality assertion
and debugging.

[DISCLAIMER]
This custom logging system `may` blow up and swallow the rest of the logging process
(and sometimes even messes with retry loops, signal handling, etc., 
depending on how tightly things are coupled).
"""

import re 
import logging
from rich.console import Console
from rich.theme import Theme
from rich.logging import RichHandler

from client.config import load_config

# Define a custom vivid theme
custom_theme = Theme({
    "logging.level.debug": "cyan",
    "logging.level.info": "bold bright_white",
    "logging.level.info": "bold bright_green",
    "logging.level.warning": "bold yellow",
    "logging.level.error": "bold red",
    "logging.level.critical": "bold reverse red",
})

# Create a console using the custom theme
custom_console = Console(theme=custom_theme)

class PurplePrefixRichHandler(RichHandler):
    def emit(self, record: logging.LogRecord) -> None:
        # Save original message
        original_msg = record.getMessage()

        # Try to extract a prefix (e.g., "rmq_manager_conn: some message")
        match = re.match(r"^(.*?):\s(.*)", original_msg)
        if match:
            prefix, rest = match.groups()
            # Pad prefix to a fixed width (e.g., 20 characters)
            padded_prefix = f"{prefix:<20}"
            # Rewrite the message to include colored prefix
            record.msg = f"[purple]{padded_prefix}[/purple]: {rest}"
            # record.args = None  # Avoid issues with %-formatting
            record.args = () # fixes websocket conn
        else:
            # Keep it unchanged if no prefix found
            record.msg = original_msg
            record.args = ()  # <- just in case this branch gets used too

        super().emit(record)

# Get the log level from the config and convert it to a valid logging level
log_level = load_config().get("LOG_LEVEL", "INFO").upper()

# Map string log level to the logging module's level constant (dispatch logic)
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Configure logging
logging.basicConfig(
    level=log_level_map.get(log_level, logging.INFO),
    format="%(message)s",  # No timestamp or extra fields
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[PurplePrefixRichHandler(
        console=custom_console,
        markup=True,
        rich_tracebacks=True,
        show_path=False
    )]
)

# Silence AMQP & Mongo related noise aggressively before anything else
for noisy in [
    # rmq noise
    "aio_pika", 
    "aio_pika.connection",
    "aio_pika.channel",
    "aio_pika.robust_connection",
    "aio_pika.robust_channel",
    "aio_pika.exchange",
    "aio_pika.queue",
    "aiormq",  # <-- this is crucial
    "pamqp",
    "pika",
    # mongo noise
    "motor",
    "pymongo",
    "pymongo.monitoring",
    "pymongo.pool",
    "pymongo.server",
    "pymongo.topology",
    "pymongo.mongo_client",
    "pymongo.connection",
    "pymongo.cursor",
    "pymongo.heartbeat",
    # httpx/httpcore noise
    "httpx",
    "httpcore",
    "h11",
    # websockets noise
    "websockets",
    "websockets.protocol",
    "websockets.server",
    "websockets.client",
    "websockets.handshake",
    "websockets.connection",
    # anyio (used for async networking underneath httpx/websockets)
    "anyio",
    "anyio._core",
    "anyio._backends._asyncio",
    "anyio._backends._trio",
]:
    log = logging.getLogger(noisy)
    log.setLevel(logging.CRITICAL + 1)  # Beyond CRITICAL
    log.handlers.clear()
    log.propagate = False

logger = logging.getLogger(__name__)