# server/auth/core.py

"""
Auth validation & JWT logic
-x-x-
[PATCH]

- Auth: Replace with a more robust mechanism when deploying to prod.
"""

import jwt

from server.config import CONFIG
from datetime import datetime, timedelta, timezone

def validate_agent_credentials(system_uuid: str, password: str) -> bool:
    # Implement logic to validate the user credentials
    # For example, check against a database or a combo of uuid + password
    # The following compares password with a hardcoded password and returns bool
    return password == CONFIG["AGENT_AUTHPASS"]  # Replace with actual validation later

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=CONFIG["ACCESS_TOKEN_EXPIRE_MINUTES"])
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CONFIG["JWT_KEY"], algorithm=CONFIG["ALGORITHM"])
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, CONFIG["JWT_KEY"], algorithms=[CONFIG["ALGORITHM"]]) # a list is needed here for algorithms
        return payload
    except jwt.PyJWTError:
        return None
    
def verify_agent_uuid(system_uuid, token_uuid):
    return system_uuid == token_uuid