# server/config/config.py

"""
Main configuration file
-x-x-
To manage app configuration from one place.

- Define your dynamic variables (networking, constants & secrets) here.
- Use sensible defaults for development & make sure to not reveal secrets
  when deploying to production.
"""

import os

"""
[PATCH]
Env file setup; will be deprecated after containerization
"""
from dotenv import load_dotenv
load_dotenv()  # load environment variables from .env file located at project root

CONFIG = {
    # AUTH
    "AGENT_AUTHPASS": os.getenv("AGENT_AUTHPASS", "treacle_authpass"),
    # JWT
    "JWT_KEY": os.getenv("JWT_KEY", "84Cfe@GjsysF?s/u(o`nZ@Ak*W@0^h"),  # Use a strong secret key
    "ALGORITHM": "HS256",  # JWT algorithm
    "ACCESS_TOKEN_EXPIRE_MINUTES": 60,  # Token expiration time
    
    # LOGGING
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO").upper(),  # default to INFO if not set in .env

    # DATABASE
    # "MONGO_URL": os.getenv("MONGO_URL", "mongodb://localhost:27017"),
    "MONGO_URL": os.getenv(
        "MONGO_URL",
        "mongodb://localhost:27017/?connectTimeoutMS=3000&socketTimeoutMS=3000"
        ),
    "MONGO_ROOT_DB": os.getenv("MONGO_ROOT_DB", "trex_db"),

    # RabbitMQ
    "RMQ_HOST": os.getenv("RMQ_HOST", "localhost"),
    "RMQ_USER": os.getenv("RMQ_USER", "guest"),
    "RMQ_PASS": os.getenv("RMQ_PASS", "guest")
}