# server/comms/mongo_manager.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
import asyncio

from server.config import CONFIG, logger

class MongoManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MongoManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.client = None
            self.db = None
            self.connected = False
            self.initialized = True

    async def connect_to_mongo(self):
        try:
            self.client = AsyncIOMotorClient(CONFIG["MONGO_URL"])
            self.db = self.client[CONFIG["MONGO_ROOT_DB"]]

            # Force early connection validation with timeout
            await asyncio.wait_for(self.client.admin.command("ping"), timeout=3.0)

            self.connected = True
            logger.info("mongo_manager: connected to MongoDB successfully.")

        except (PyMongoError, asyncio.TimeoutError) as e:
            self.connected = False
            logger.error(f"mongo_manager: failed to connect to MongoDB: {e}")
            raise RuntimeError("mongo_manager: MongoDB connection failed. Shutting down.")
    
    def get_db(self):
        if self.db is None:
            raise RuntimeError("mongo_manager: Database not initialized. Did you forget to call connect_to_mongo()?")

        return self.db
    
    async def close(self):
        try:
            if self.client:
                self.client.close()
                logger.info("mongo_manager: MongoDB connection closed.")
        except Exception as e:
            logger.warning(f"mongo_manager: failed to close MongoDB connection: {e}")

# Singleton instance to use across app
mongo_manager_conn = MongoManager()
