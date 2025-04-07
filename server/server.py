# server/server.py

"""
Server logic
-x-x-
Central server app; All agents connect here.

- Authenticates agents with JWT.
- Establishes websocket comms with agents.
- Connects to RabbitMQ (task allocation & data streaming).
- Stores telemetry & interaction data in Mongo.
"""
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI

from server.decorators.json_response import json_response
from server.config import logger
from server.auth import auth_router
from server.comms import (
    rmq_manager_conn,
    mongo_manager_conn
)

"""
FastAPI Lifespan
-x-x-
Lifespan here is used to manage resources that need to be
initialized when the app starts or shuts down.

The following objects are created & used as a shared instance 
app-wide.

- WebsocketConnectionManager
- RabbitMQConnectionManager
- MongoMotorClient
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    try:
        await rmq_manager_conn.connect_to_rabbit()
        await mongo_manager_conn.connect_to_mongo()
    except RuntimeError:
        logger.error("server: RabbitMQ/Mongo services are down. Application cannot start.")
        sys.exit(1)
    
    try:
        # --- Yield to app ---
        yield
    finally:
        # --- Shutdown Logic ---
        sys.stdout.write("\n")        # move to next line
        sys.stdout.write("\033[F")    # move cursor up one line
        sys.stdout.write("\033[K")    # clear the line
        logger.info("server: shutting down server... /ws/ will be closed")

        # Clean up connections
        await mongo_manager_conn.close()
        await rmq_manager_conn.close()

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/auth")

# root as healthcheck endpoint
@app.get("/")
@json_response(status_code=200)
async def healthcheck():
    logger.debug("server: healthcheck endpoint hit!")
    return "healthy"

ascii_art = r"""
  ___                                      .-~. /_"-._
`-._~-.                                  / /_ "~o\  :Y
      \  \                                / : \~x.  ` ')
      ]  Y                              /  |  Y< ~-.__j
     /   !                        _.--~T : l  l<  /.-~
    /   /                 ____.--~ .   ` l /~\ \<|Y
   /   /             .-~~"        /| .    ',-~\ \L|
  /   /             /     .^   \ Y~Y \.^>/l_   "--'
 /   Y           .-"(  .  l__  j_j l_/ /~_.-~    .
Y    l          /    \  )    ~~~." / `/"~ / \.__/l_
|     \     _.-"      ~-{__     l  :  l._Z~-.___.--~                   ^~~: 
|      ~---~           /   ~~"---\_  ' __[>              .~!!!^   .. :7!.:J:
l  .                _.^   ___     _>-y~          ...    :J:  .?7~.:^.:^!~~~ 
 \  \     .      .-~   .-~   ~>--"  /           ~^:^~.  :J!~^:J!  
  \  ~---"            /     ./  _.-'           .7.  7~::~7!7?~~7. 
   "-.,_____.,_  _.--~\     _.-~                .^^^:   .~::.   .7^:^^^: 
               ~~     (   _}      |T-REX    |         :^^        ^J~^::~7^
                      `. ~(       |FRAMEWORK|        ^!~~        J^     :Y.
                        )  \                         \.:         !7.   .!7
                  /,`--'~\--'~\                                   ^!!!!!^ 
                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import random

# Define colors
colors = [
    '\033[92m',  # Green
    '\033[94m',  # Blue
    '\033[91m',  # Red
]
reset = '\033[0m'

# Select one random color from the list
selected_color = random.choice(colors)

# Print all lines in that chosen color
for line in ascii_art.splitlines():
    print(selected_color + line + reset)
