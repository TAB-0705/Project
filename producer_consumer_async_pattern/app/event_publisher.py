"""The PRODUCER half of the pattern, and the only module that talks to Azure
Service Bus. It publishes a 'todo_created' event to the queue whenever a todo
is created.

Graceful fallback: if no connection string is configured, it logs the event
instead of sending — so the API runs locally without Azure, and the rest of
the code never has to know whether the bus is wired up.
"""

import json
import logging

from .config import SERVICE_BUS_CONNECTION_STRING, SERVICE_BUS_QUEUE_NAME

logger = logging.getLogger("event_publisher")
logging.basicConfig(level=logging.INFO)


async def publish_todo_created(todo: dict) -> None:
    event = {"event": "todo_created", "data": todo}
    body = json.dumps(event)

    # Fallback path: no Service Bus configured.
    if not SERVICE_BUS_CONNECTION_STRING:
        logger.warning("Service Bus not configured; event NOT sent: %s", body)
        return

    # Real path: send to the queue using the async client.
    from azure.servicebus.aio import ServiceBusClient
    from azure.servicebus import ServiceBusMessage

    async with ServiceBusClient.from_connection_string(
        SERVICE_BUS_CONNECTION_STRING
    ) as client:
        sender = client.get_queue_sender(queue_name=SERVICE_BUS_QUEUE_NAME)
        async with sender:
            await sender.send_messages(ServiceBusMessage(body))
    logger.info("Published event to '%s': %s", SERVICE_BUS_QUEUE_NAME, body)
