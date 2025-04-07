# server/config/rich_logger.py

"""
Rich logger configuration
-x-x-
A custom logger configuration for functionality assertion
and debugging.
"""
import re 
import logging
from rich.console import Console
from rich.theme import Theme
from rich.logging import RichHandler

from .config import CONFIG  # Import the configuration

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
            record.args = None  # Avoid issues with %-formatting
        else:
            # Keep it unchanged if no prefix found
            record.msg = original_msg

        super().emit(record)

# Get the log level from the config and convert it to a valid logging level
log_level = CONFIG.get("LOG_LEVEL", "INFO").upper()

# Map string log level to the logging module's level constant (dispatch logic)
log_level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# # Set up logging with dynamic log level
# logging.basicConfig(
#     level=log_level_map.get(log_level, logging.INFO),  # Default to INFO if invalid level
#     format="%(message)s",  # Remove timestamp here
#     datefmt="[%Y-%m-%d %H:%M:%S]",  # This is for the timestamp format of the log message
#     handlers=[RichHandler(
#         console=custom_console,
#         markup=True,
#         rich_tracebacks=True,
#         show_path=False
#     )]
# )

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

# Suppress logs for Uvicorn
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.asgi").setLevel(logging.CRITICAL)

# print("\n[🐛 Active Loggers]")
# for name, logger in logging.root.manager.loggerDict.items():
#     if hasattr(logger, 'level'):
#         print(f"{name}: level={logging.getLevelName(logger.level)}, handlers={logger.handlers}, propagate={logger.propagate}")

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
    "pymongo.heartbeat"
]:
    log = logging.getLogger(noisy)
    log.setLevel(logging.CRITICAL + 1)  # Beyond CRITICAL
    log.handlers.clear()
    log.propagate = False


logger = logging.getLogger(__name__)