# server/gql/client_info/queries.py

import strawberry

from typing import Optional

from .models import ClientStatus

# mongo setup
from server.comms.mongo_manager import mongo_manager_conn

@strawberry.type
class ClientInfo:
    @strawberry.field
    async def get_client_status(
        self, 
        system_uuid: Optional[str] = None,  # Optional: can be None to retrieve all clients
        org: Optional[str] = None           # Optional: filter by organization if provided
    ) -> list[ClientStatus]:  # Return a list of clients
        agent_status_col = mongo_manager_conn.get_db()["agent_status"]
        
        # Build the query
        query = {}
        if system_uuid:
            query["system_uuid"] = system_uuid  # Filter by system_uuid if provided
        if org:
            query["org"] = org  # Filter by org if provided
        
        # Retrieve matching clients
        result = await agent_status_col.find(query).to_list(None)
        
        # If results are found, map them to ClientStatus
        if result:
            return [
                ClientStatus(
                    _id=str(client["_id"]),  # Convert ObjectId to string
                    system_uuid=client["system_uuid"], 
                    org=client["org"],
                    status=client["status"],
                    connected_at=client["connected_at"],
                    last_disconnected=client.get("last_disconnected")
                ) for client in result
            ]
        
        # If no results are found, return an empty list
        return []