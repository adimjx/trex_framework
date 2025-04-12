import strawberry
from datetime import datetime
from typing import Optional

@strawberry.type
class ClientStatus:
    _id: Optional[str]  # MongoDB's ObjectId as a string
    system_uuid: str
    org: Optional[str]  # Optional, in case it's not found in MongoDB
    status: str
    connected_at: Optional[datetime]  # Make it optional to handle null values
    last_disconnected: Optional[datetime]  # Optional field (nullable)