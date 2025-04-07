# server/comms/rmq_manager.py

"""
RMQ Manager
-x-x-
This module follows the Singleton design pattern to manage the RabbitMQ connection.
Only a single instance of the RMQManager class is created, ensuring that the RabbitMQ
connection is shared app-wide and reused throughout the application.
"""

import aio_pika

from server.config import CONFIG, logger

class RMQManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RMQManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.rabbit_connection = None
            self.channels = {}  # Replaces the old self.channel
            self.queues = {}
            self.rabbit_connected = False
            self.initialized = True

    async def connect_to_rabbit(self):
        try:
            self.rabbit_connection = await aio_pika.connect_robust(
                f"amqp://{CONFIG['RMQ_USER']}:{CONFIG['RMQ_PASS']}@{CONFIG['RMQ_HOST']}/"
            )

            # Define your logical channel groups
            """
            queues can be grouped logically by assigning them to different channels in your app,
            even though RabbitMQ doesnt enforce or name channels internally.

            channel-based logical grouping = smart design

            channel = rmq_manager.get_channel("telemetry")
            queue = await channel.declare_queue("some_telemetry_queue", durable=True)
            """
            self.channels = {
                "action": await self.rabbit_connection.channel(),
                "telemetry": await self.rabbit_connection.channel(),
                "filestream": await self.rabbit_connection.channel()
            }

            self.rabbit_connected = True
            logger.info("rmq_manager_conn: connected to RabbitMQ and initialized logical channels.")

        except Exception as e:
            self.rabbit_connected = False
            logger.error(f"rmq_manager_conn: failed to connect to RabbitMQ: {e}")
            raise RuntimeError("rmq_manager_conn: rabbitMQ connection failed. Shutting down.")

    def get_channel(self, name: str):
        channel = self.channels.get(name)
        if not channel:
            logger.warning(f"rmq_manager_conn: requested RMQ channel '{name}' does not exist.")
        return channel
    
    async def close(self):
        try:
            if self.rabbit_connection and not self.rabbit_connection.is_closed:
                await self.rabbit_connection.close()
                logger.info("rmq_manager_conn: RabbitMQ connection closed.")
        except Exception as e:
            logger.warning(f"rmq_manager_conn: failed to close RabbitMQ connection: {e}")
    
# app-wide RMQ connection object (singleton instance)
rmq_manager_conn = RMQManager()
