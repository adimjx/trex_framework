# client/comms/rmq_manager.py

import aio_pika
from client.config import load_config, logger
config = load_config()

class ClientRMQManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ClientRMQManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.rabbit_connection = None
            self.channels = {}
            self.queues = {}
            self.rabbit_connected = False
            self.initialized = True

    async def connect_to_rabbit(self, systemuuid):
        try:
            self.rabbit_connection = await aio_pika.connect_robust(
                f"amqp://{config['RMQ_USER']}:{config['RMQ_PASS']}@{config['RMQ_HOST']}/"
            )

            self.channels = {
                "action": await self.rabbit_connection.channel(),
                "telemetry": await self.rabbit_connection.channel(),
                "filestream": await self.rabbit_connection.channel()
            }

            # Declare queues per logical use
            self.queues["action"] = await self.channels["action"].declare_queue(
                f"action_{systemuuid}", durable=True
            )

            self.queues["proc_telemetry"] = await self.channels["telemetry"].declare_queue(
                f"proc_telemetry_{systemuuid}", durable=True
            )

            self.queues["filestream_in"] = await self.channels["filestream"].declare_queue(
                f"filestream_in_{systemuuid}", durable=True
            )

            self.queues["filestream_out"] = await self.channels["filestream"].declare_queue(
                f"filestream_out_{systemuuid}", durable=True
            )

            self.rabbit_connected = True
            logger.info("client_rmq_manager: connected to RabbitMQ and initialized logical channels/queues.")

        except Exception as e:
            self.rabbit_connected = False
            logger.error(f"client_rmq_manager: failed to connect to RabbitMQ: {e}")
            raise RuntimeError("client_rmq_manager: connection to RabbitMQ failed.")

    def get_channel(self, name: str):
        return self.channels.get(name)

    def get_queue(self, name: str):
        return self.queues.get(name)

    async def close(self):
        try:
            if self.rabbit_connection and not self.rabbit_connection.is_closed:
                await self.rabbit_connection.close()
                logger.info("client_rmq_manager: RabbitMQ connection closed.")
        except Exception as e:
            logger.warning(f"client_rmq_manager: error while closing RabbitMQ connection: {e}")

# Singleton instance
client_rmq_manager = ClientRMQManager()
