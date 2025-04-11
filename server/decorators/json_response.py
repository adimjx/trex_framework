# server/decorators/json_resp.py

"""
Generic JSON response decorator
-x-x-
Wraps the return dict/string in a standard format.
"""

from fastapi.responses import JSONResponse
from functools import wraps
from typing import Callable


def json_response(status_code: int = 200):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            if isinstance(result, dict):
                message = result.get("message", "success")
                # Remove 'message' key from result to avoid redundancy in data
                data = {key: value for key, value in result.items() if key != "message"}  # exclude 'message' from data
            elif isinstance(result, str):
                message = result  # use the string as the message
                data = {}  # set data to an empty object (empty dict) or None
            else:
                message = "success"  # default message for other types
                data = {}  # set data to an empty object (empty dict) or None

            return JSONResponse(
                status_code=status_code,
                content={
                    "status": "ok",
                    "message": message,
                    "data": data,  # this will include the result in the "data" field or empty object
                }
            )
        return wrapper
    return decorator